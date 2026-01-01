import logging
import asyncio
import json
from typing import Any, Optional
from dataclasses import dataclass

import yfinance as yf
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from sqlalchemy import select
from collections.abc import AsyncIterator

from mvp.app.config.settings import settings
from mvp.app.services.router_service import RouterService, Intent, get_router_service
from mvp.app.services.search_service import SearchService, SearchResult, get_search_service
from mvp.app.services.memory_service import MemoryService, get_memory_service
from mvp.app.db.database import get_session_context
from mvp.app.models.chat_source_model import ChatSource
from mvp.app.models.chat_model import ChatMessage

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================
def merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dictionaries. Used for Reducer."""
    if not left: left = {}
    if not right: right = {}
    return {**left, **right}

def get_favicon(url: str) -> str:
    """Generate Google Favicon URL for a given domain."""
    try:
        from urllib.parse import urlparse
        if not url.startswith("http"):
            url = "http://" + url
        domain = urlparse(url).netloc
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    except Exception:
        return "https://www.google.com/s2/favicons?domain=example.com"

class AgentState(TypedDict):
    """State that flows through the agent graph."""
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    intent: list[str]              # Classified intents (LIST)
    tool_results: Annotated[dict, merge_dicts] # Reducer for parallel execution
    context: str                   # Formatted context for LLM
    stm_history: list[dict]        # Short-term memory (sliding window)
    has_files: bool                # Whether session has files uploaded
    refined_prompt: str            # Optimized prompt from the refiner model
    summary: str                   # Conversation summary (background generated)


# =============================================================================
# Chat Service
# =============================================================================
class ChatService:
    """
    Agentic chat service with intelligent routing, prompt refinement, and multi-source retrieval.
    """
    
    # How many messages before we trigger a summary update
    SUMMARY_THRESHOLD = 10
    
    def __init__(
        self,
        main_model: str = None,
        refiner_model: str = None,
        system_prompt: str = None,
    ):
        self.main_model = main_model or settings.main_model or "llama-3.3-70b-versatile"
        self.refiner_model = refiner_model or settings.refiner_model or "llama-3.1-8b-instant"
        self.system_prompt = system_prompt or "You are a helpful, knowledgeable assistant."
        
        # Services (initialized on connect)
        self._router: Optional[RouterService] = None
        self._search: Optional[SearchService] = None
        self._history: Optional[VectorService] = None # Vector History
        self._memory: Optional[MemoryService] = None
        self._main_llm: Optional[ChatGroq] = None
        self._refiner_llm: Optional[ChatGroq] = None
        
        # Compiled graph
        self._app = None
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    async def connect(self):
        """Initialize all services and build graph."""
        # Router
        self._router = get_router_service()
        
        # Search (Tavily + Qdrant for Docs)
        self._search = await get_search_service()
        
        # History (Qdrant for Chat Logs)
        # We need a dedicated VectorService instance for history
        from mvp.app.utils.vector_service import VectorService
        self._history = VectorService(collection_name="chat_history")
        await self._history.connect()
        
        # Memory (Valkey + Mem0)
        self._memory = await get_memory_service()
        
        # Main LLM (High-end)
        self._main_llm = ChatGroq(
            model=self.main_model,
            api_key=settings.llm_api_key,
            temperature=0.7,
        )
        
        # Refiner LLM (Low-end/Fast)
        self._refiner_llm = ChatGroq(
            model=self.refiner_model,
            api_key=settings.llm_api_key,
            temperature=0.3, # Lower temperature for stable rewriting
            max_tokens=300,
        )
        
        # Build graph
        self._app = self._build_graph()
        
        logger.info(f"ChatService: Connected (Main={self.main_model}, Refiner={self.refiner_model})")
    
    async def close(self):
        """Close all service connections."""
        if self._search:
            await self._search.close()
        if self._history:
            await self._history.close()
        if self._memory:
            await self._memory.close()
        logger.info("ChatService: Closed")
    
    # =========================================================================
    # Graph Nodes
    # =========================================================================
    async def _load_stm(self, state: AgentState) -> dict:
        """Load short-term memory (conversation history) from Valkey."""
        session_id = state.get("session_id")
        
        try:
            history = await self._memory.get_stm(session_id, limit=10)
            
            # Also check if user has files for this session
            has_files = False
            async with get_session_context() as db:
                result = await db.execute(select(ChatSource).where(ChatSource.session_id == session_id).limit(1))
                if result.scalars().first():
                    has_files = True
            
            # Load Summary
            summary = await self._memory.get_summary(session_id)
            
            return {"stm_history": history, "has_files": has_files, "summary": summary}
        except Exception as e:
            logger.error(f"Load STM error: {e}")
            return {"stm_history": [], "has_files": False, "summary": None}
    
    async def _analyze(self, state: AgentState) -> dict:
        """Analyze user intent using RouterService."""
        messages = state.get("messages", [])
        history = state.get("stm_history", [])
        has_files = state.get("has_files", False)
        
        if not messages:
            return {"intent": Intent.DIRECT_ANSWER.value}
        
        # Get last user message
        last_message = messages[-1]
        content = last_message.content if hasattr(last_message, "content") else str(last_message)
        
        intent = await self._router.classify(content, history, has_files=has_files)
        return {"intent": intent}
    
    async def _tool_web_search(self, state: AgentState) -> dict:
        """Execute web search via Tavily."""
        messages = state.get("messages", [])
        if not messages:
            return {"tool_results": state.get("tool_results", {})}
        
        query = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        # Increased limit for more sources
        results = await self._search.web_search(query, limit=7)
        
        current_results = state.get("tool_results", {})
        current_results = state.get("tool_results", {})
        current_results["web"] = [{
            "content": r.content, 
            "source": r.source, 
            "title": r.title,
            "favicon": get_favicon(r.source)
        } for r in results]
        
        return {"tool_results": current_results}
    
    async def _tool_rag_search(self, state: AgentState) -> dict:
        """Execute RAG search via Qdrant."""
        messages = state.get("messages", [])
        user_id = state.get("user_id")
        session_id = state.get("session_id")
        
        if not messages:
            return {"tool_results": state.get("tool_results", {})}
        
        query = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        # Search using both user_id and session_id context
        results = await self._search.rag_search(query, user_id=user_id, session_id=session_id, limit=3)
        
        current_results = state.get("tool_results", {})
        current_results = state.get("tool_results", {})
        current_results["rag"] = [{
            "content": r.content, 
            "source": r.source, 
            "title": r.title,
            "favicon": "https://www.google.com/s2/favicons?domain=adobe.com" # Generic PDF/Doc icon
        } for r in results]
        
        return {"tool_results": current_results}
    
    async def _tool_memory_recall(self, state: AgentState) -> dict:
        """Recall from long-term memory (Mem0) AND search past chat history in DB."""
        messages = state.get("messages", [])
        user_id = state.get("user_id")
        session_id = state.get("session_id")
        
        if not messages or not user_id:
            return {"tool_results": state.get("tool_results", {})}
        
        query = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        # 1. Search Mem0 (Facts/Preferences)
        mem_results = await self._memory.get_ltm(user_id, query, limit=3)
        formatted_memories = [{"content": r.get("memory", ""), "score": r.get("score", 0)} for r in mem_results]
        
        # 2. Search Vector History (Semantic Recall)
        # This replaces the old DB ILIKE search with SDE-3 level Vector Search
        history_matches = []
        try:
            # Search for relevant past messages using embeddings
            # We filter by user_id to ensure privacy/scope
            if self._history:
                results = await self._history.search(
                    query, 
                    limit=5, 
                    user_id=user_id
                )
                
                for res in results:
                    # Format: [Role] Content
                    # We can use metadata to get role and timestamp if available
                    meta = res.get("metadata", {})
                    role = meta.get("role", "unknown")
                    ts = meta.get("timestamp", "")
                    content = res.get("content", "")
                    history_matches.append(f"[{role.upper()}] {content}")
                    
        except Exception as e:
            logger.error(f"Vector History Search failed: {e}")

        current_results = state.get("tool_results", {})
        
        # Combine results
        current_results["memory"] = formatted_memories
        if history_matches:
            # Append history matches as a special memory type or just append to memory list
            # We'll add a structured item for the context builder to handle
            current_results["history_matches"] = history_matches
            
        return {"tool_results": current_results}
        
    async def _tool_finance(self, state: AgentState) -> dict:
        """Fetch stock market data using yfinance."""
        messages = state.get("messages", [])
        if not messages:
            return {"tool_results": state.get("tool_results", {})}
            
        content = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        # 1. Extract ticker from message using LLM
        prompt = f"""Extract the stock ticker symbol(s) for the query: "{content}".
        Rules:
        1. Return ONLY the ticker symbol(s), separated by comma if multiple.
        2. For Indian companies (NSE/BSE), YOU MUST append '.NS' (e.g. "TCS" -> "TCS.NS", "Reliance" -> "RELIANCE.NS", "Infosys" -> "INFY.NS").
        3. For US companies, use the standard ticker (e.g. "Apple" -> "AAPL").
        4. If the user mentions a full company name, map it to the correct ticker.
        5. If unsure or no financial entity found, return 'NONE'.
        
        Examples:
        "price of tcs" -> "TCS.NS"
        "infosys and wipro" -> "INFY.NS, WIPRO.NS"
        "tesla stock" -> "TSLA"
        """
        
        try:
            extraction = await self._main_llm.ainvoke([HumanMessage(content=prompt)])
            ticker_symbol = extraction.content.strip()
            
            if "NONE" in ticker_symbol or len(ticker_symbol) > 10:
                logger.warning(f"Could not extract ticker from: {content}")
                return {"tool_results": state.get("tool_results", {})}
                
            # 2. Fetch data via yfinance (async safe)
            logger.info(f"Fetching finance data for: {ticker_symbol}")
            
            def fetch_stock():
                ticker = yf.Ticker(ticker_symbol)
                history = ticker.history(period="1d")
                info = ticker.info
                price = history['Close'].iloc[-1] if not history.empty else info.get('currentPrice', 'N/A')
                currency = info.get('currency', 'USD')
                name = info.get('longName', ticker_symbol)
                return {
                    "symbol": ticker_symbol,
                    "price": price,
                    "currency": currency,
                    "name": name,
                    "full_info": json.dumps(info)[:500] + "..." # Truncate for context
                }
            
            stock_data = await asyncio.to_thread(fetch_stock)
            
            current_results = state.get("tool_results", {})
            current_results["finance"] = [{
                "content": f"Live Data for {stock_data['name']} ({stock_data['symbol']}): Price = {stock_data['price']} {stock_data['currency']}",
                "title": f"Stock Price: {stock_data['symbol']}",
                "source": "https://finance.yahoo.com",
                "favicon": get_favicon("https://finance.yahoo.com"),
                "data": stock_data
            }]
            return {"tool_results": current_results}
            
        except Exception as e:
            logger.error(f"Finance tool error: {e}")
            return {"tool_results": state.get("tool_results", {})}
    
    async def _build_context(self, state: AgentState) -> dict:
        """Build context string from tool results and STM."""
        tool_results = state.get("tool_results", {})
        stm_history = state.get("stm_history", [])
        
        context_parts = []
        
        # Add conversation history (STM)
        if stm_history:
            history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in stm_history[-5:]])
            context_parts.append(f"CONVERSATION HISTORY:\n{history_text}")
        
        # Add web results
        web_results = tool_results.get("web", [])
        if web_results:
            web_text = "\n\n".join([f"[{r['title']}] ({r['source']})\n{r['content']}" for r in web_results])
            context_parts.append(f"WEB SEARCH RESULTS:\n{web_text}")
        
        # Add RAG results
        rag_results = tool_results.get("rag", [])
        if rag_results:
            rag_text = "\n\n".join([f"[{r['title']}]\n{r['content']}" for r in rag_results])
            context_parts.append(f"DOCUMENT SEARCH RESULTS:\n{rag_text}")
            
        # Add Financial results
        fin_results = tool_results.get("finance", [])
        if fin_results:
            fin_text = "\n".join([f"{r['content']}" for r in fin_results])
            context_parts.append(f"FINANCIAL DATA:\n{fin_text}")
        
        # Add memory results
        mem_results = tool_results.get("memory", [])
        history_matches = tool_results.get("history_matches", [])
        
        mem_text = ""
        if mem_results:
            mem_text += "Facts/Preferences:\n" + "\n".join([f"- {r['content']}" for r in mem_results])
        
        if history_matches:
            if mem_text: mem_text += "\n\n"
            mem_text += "Related Past Conversation:\n" + "\n".join(history_matches)
            
        if mem_text:
            context_parts.append(f"MEMORY & HISTORY:\n{mem_text}")
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else ""
        
        return {"context": context}
    
    async def _refine_prompt(self, state: AgentState) -> dict:
        """Refine the user's prompt using the low-cost model."""
        messages = state.get("messages", [])
        if not messages:
            return {}
            
        original_prompt = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        refine_system = """You are an expert Prompt Engineer.
        Your goal is to optimize the user's query for a Large Language Model to ensure the best possible answer.
        
        Instructions:
        1. Make the query more specific, detailed, and clear.
        2. Fix any grammar or ambiguity.
        3. If there is context (e.g. search results), explicitly mention it in the prompt instructions.
        4. KEEP the original intent exactly the same. Do not answer the question yourself.
        
        CRITICAL: Output ONLY the rewritten prompt text. Do NOT add "Here is the refined prompt" or any explanation.
        Do NOT use quotes around the output. Just the raw text."""
        
        try:
            # We pass context implicitly via the system prompt design, 
            # or we could append "Note: The user provided search results are available."
            refined = await self._refiner_llm.ainvoke([
                SystemMessage(content=refine_system),
                HumanMessage(content=f"Rewrite this query: {original_prompt}")
            ])
            
            refined_text = refined.content.strip()
            logger.info(f"Refined Prompt: '{original_prompt}' -> '{refined_text}'")
            return {"refined_prompt": refined_text}
            
        except Exception as e:
            logger.error(f"Prompt Refinement failed: {e}")
            return {"refined_prompt": original_prompt}

    async def _generate(self, state: AgentState) -> dict:
        """Generate response using main LLM."""
        context = state.get("context", "")
        messages = state.get("messages", [])
        user_id = state.get("user_id", "unknown")
        refined_prompt = state.get("refined_prompt", "")
        
        # Build system prompt with context
        final_system = self.system_prompt
        
        # Inject Summary if available
        summary = state.get("summary")
        if summary:
            final_system += f"\n\nPREVIOUS CONVERSATION SUMMARY:\n{summary}"
            
        if context:
            final_system += f"\n\nCONTEXT (this information is retrieved from tools):\n{context}"
        
        # Build message list
        llm_messages = [SystemMessage(content=final_system)]
        
        # Add STM for conversational coherence
        for msg in state.get("stm_history", [])[-5:]:
            if msg["role"] == "user":
                llm_messages.append(HumanMessage(content=msg["content"]))
            else:
                llm_messages.append(AIMessage(content=msg["content"]))
        
        # Add current message (Use REFINED PROMPT if available)
        if refined_prompt:
             llm_messages.append(HumanMessage(content=f"[Original Query: {messages[-1].content}]\n[Optimized Query]: {refined_prompt}"))
        else:
            for msg in messages:
                if hasattr(msg, "content"):
                    llm_messages.append(msg)
                else:
                    llm_messages.append(HumanMessage(content=str(msg)))
        
        try:
            response = await self._main_llm.ainvoke(llm_messages)
            logger.info(f"Generate: user={user_id} | tokens={len(str(response.content))//4}")
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Generate error: {e}")
            return {"messages": [AIMessage(content="I apologize, but I encountered an error. Please try again.")]}
    
    async def save_session_background(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        sources: list[dict] = None
    ):
        """
        Background task to persist chat to DB and Memory.
        This runs AFTER the response has been streamed to the user.
        """
        try:
            # 1. Save to STM (Valkey)
            if user_message:
                await self._memory.add_stm(session_id, "user", user_message)
            if ai_response:
                await self._memory.add_stm(session_id, "assistant", ai_response)
            
            # 2. Save to Postgres (if not handled by API layer, but API layer usually handles raw message)
            # NOTE: The API layer (chat.py) handles the Postgres DB Save for the Message History.
            # We only need to handle the Semantic/Vector history here if we want to decoupling it.
            # However, for this architecture, let's keep the API layer doing the SQL save, 
            # and this worker doing the Vector/LTM save.
            
            # 3. LTM Extraction (Mem0)
            if user_message and any(kw in user_message.lower() for kw in ["i prefer", "i like", "remember that", "my name is", "i am"]):
                await self._memory.add_ltm(user_id, user_message)
            
            # 4. Vector History (Qdrant)
            if self._history:
                import datetime
                timestamp = datetime.datetime.utcnow().isoformat()
                
                to_embed = []
                metadatas = []
                
                if user_message:
                    to_embed.append(user_message)
                    metadatas.append({
                        "user_id": user_id, 
                        "session_id": session_id, 
                        "role": "user",
                        "timestamp": timestamp
                    })
                
                if ai_response:
                    to_embed.append(ai_response)
                    metadatas.append({
                        "user_id": user_id, 
                        "session_id": session_id, 
                        "role": "assistant", 
                        "timestamp": timestamp,
                        "sources": json.dumps(sources) if sources else "[]"
                    })
                
                if to_embed:
                    await self._history.add_texts(to_embed, metadatas)
                    
            logger.info(f"Background persistence complete for session {session_id}")
            
            # 5. Background Summarization (Optimization)
            # Check if we need to summarize (e.g. every N messages)
            # We can check total messages in STM or just run randomly/periodically
            # For efficiency: get count from stm
            current_history = await self._memory.get_stm(session_id, limit=100)
            if len(current_history) >= self.SUMMARY_THRESHOLD:
                # We should summarize
                await self._summarize_background(session_id, current_history)
                
        except Exception as e:
            logger.error(f"Background persistence error: {e}")
            
    async def _summarize_background(self, session_id: str, history: list[dict]):
        """Generate a summary of the conversation and save to memory."""
        try:
            logger.info(f"Starting background summarization for {session_id}")
            
            # Use Refiner Model (Cheap)
            prompt = "Summarize the following conversation in 3-4 concise sentences, capturing key facts and user intent:\n\n"
            text_block = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
            
            if len(text_block) > 6000: # Truncate if too huge
                text_block = text_block[-6000:]
                
            messages = [
                SystemMessage(content="You are a helpful conversation summarizer."),
                HumanMessage(content=prompt + text_block)
            ]
            
            response = await self._refiner_llm.ainvoke(messages)
            summary = response.content.strip()
            
            # Save to Memory
            await self._memory.set_summary(session_id, summary)
            logger.info(f"Summarization complete for {session_id}: {len(summary)} chars")
            
        except Exception as e:
            logger.error(f"Background summarization failed: {e}")
    
    # =========================================================================
    # Routing Logic
    # =========================================================================
    def _route_by_intent(self, state: AgentState) -> list[str]:
        """Determine next node(s) based on intents."""
        intents = state.get("intent", ["direct_answer"])
        # Ensure it's a list (backward compatibility if needed)
        if isinstance(intents, str):
            intents = [intents]
            
        next_nodes = []
        
        for intent in intents:
            if intent == Intent.WEB_SEARCH.value:
                next_nodes.append("tool_web")
            elif intent == Intent.RAG_SEARCH.value:
                next_nodes.append("tool_rag")
            elif intent == Intent.FINANCIAL_DATA.value:
                next_nodes.append("tool_finance")
            elif intent == Intent.MEMORY_RECALL.value:
                next_nodes.append("tool_memory")
        
        # If any tools selected, return them
        if next_nodes:
            logger.info(f"Routing to: {next_nodes}")
            return list(set(next_nodes))
        
        # Default fallback
        logger.info("Routing to: build_context (direct answer)")
        return ["build_context"]
    
    # =========================================================================
    # Graph Construction
    # =========================================================================
    def _build_graph(self):
        """Build the LangGraph agent."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("load_stm", self._load_stm)
        graph.add_node("analyze", self._analyze)
        graph.add_node("tool_web", self._tool_web_search)
        graph.add_node("tool_rag", self._tool_rag_search)
        graph.add_node("tool_finance", self._tool_finance)
        graph.add_node("tool_memory", self._tool_memory_recall)
        graph.add_node("build_context", self._build_context)
        graph.add_node("refine_prompt", self._refine_prompt) # NEW Node
        graph.add_node("generate", self._generate)
        
        # Define edges
        graph.add_edge(START, "load_stm")
        graph.add_edge("load_stm", "analyze")
        
        # Conditional routing based on intent
        graph.add_conditional_edges(
            "analyze",
            self._route_by_intent,
            {
                "tool_web": "tool_web",
                "tool_rag": "tool_rag",
                "tool_finance": "tool_finance",
                "tool_memory": "tool_memory",
                "build_context": "build_context",
            }
        )
        
        # Tools -> build_context
        graph.add_edge("tool_web", "build_context")
        graph.add_edge("tool_rag", "build_context")
        graph.add_edge("tool_finance", "build_context")
        graph.add_edge("tool_memory", "build_context")
        
        # build_context -> refine_prompt -> generate -> persist -> END
        graph.add_edge("build_context", "refine_prompt")
        graph.add_edge("refine_prompt", "generate")
        graph.add_edge("generate", END)
        
        return graph.compile()
    
    # =========================================================================
    # Public API
    # =========================================================================
    async def chat_stream(self, message: str, user_id: str, session_id: str) -> AsyncIterator[dict]:
        """
        Stream chat response token-by-token.
        
        Yields:
            Dict with keys: event_type (token, intent, source), content
        """
        if not self._app:
            await self.connect()
            
        inputs = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id,
            "intent": [],
            "tool_results": {},
            "context": "",
            "stm_history": [],
            "has_files": False,
            "refined_prompt": "",
            "summary": "",
        }
        
        # Use astream_events to catch tokens from the 'generate' node
        # We filter for 'on_chat_model_stream' events
        async for event in self._app.astream_events(inputs, version="v2"):
            kind = event["event"]
            
            # 1. Stream Tokens from the LLM
            if kind == "on_chat_model_stream":
                # Check if this event comes from the 'generate' node
                # LangGraph adds metadata about the node
                metadata = event.get("metadata", {})
                node = metadata.get("langgraph_node", "")
                
                if node == "generate":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {
                            "event_type": "token",
                            "content": content
                        }
            
            # 1.5 Capture Token Usage (End of Generation)
            elif kind == "on_chat_model_end":
                metadata = event.get("metadata", {})
                node = metadata.get("langgraph_node", "")
                if node == "generate":
                    output = event["data"].get("output")
                    if output and hasattr(output, "usage_metadata"):
                        usage = output.usage_metadata
                        if usage:
                            yield {
                                "event_type": "usage",
                                "content": usage
                            }

            # 2. Capture Tool/Intent Info (Optional, can stream intermediate status)
            elif kind == "on_chain_end" and event["name"] == "analyze":
                # Output from the analyze node
                # The output is a dict like {"intent": "web_search"}
                 # Access output correctly based on LangGraph structure
                # This might be tricky to get exactly from stream events depending on nesting
                pass
                
            # 3. Capture Sources when tool nodes finish
            elif kind == "on_tool_end":
                # If we were using standard LangChain tools, but we are using custom nodes.
                # So we watch for 'on_chain_end' of our custom nodes like '_tool_web_search'
                pass
                
            elif kind == "on_chain_end":
                node_name = event["name"]
                if node_name in ["tool_web", "tool_rag", "tool_finance", "tool_memory"]:
                     # Capture results from our custom tool nodes
                     output = event["data"].get("output")
                     if output and "tool_results" in output:
                         # The output is like {'tool_results': {'web': [...]}}
                         # We want to yield the inner lists
                         results = output["tool_results"]
                         for category, items in results.items():
                             if isinstance(items, list):
                                 # Yield each source item
                                 yield {
                                     "event_type": "source",
                                     "content": items
                                 }
        
        # At the end of the stream, we might want to yield the sources
        # But since astream_events finishes, we don't naturally have the "final state" object easily
        # unless we accumulate it or run a separate invocation (wasteful).
        # A better pattern:
        # We can yield a "meta" event at the end containing intent/sources.
        # But accessing the final state from astream_events is hard.
        # Workaround: valid streaming often involves just tokens. 
        # For sources, we can try to extract them if we see them flowing.
        pass
        
        # Note: We rely on the API layer to use the accumulated text for persistence.



# =============================================================================
# Factory function
# =============================================================================
_chat_service: Optional[ChatService] = None


async def get_chat_service() -> ChatService:
    """Get or create the global ChatService instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
        await _chat_service.connect()
    return _chat_service


# =============================================================================
# Test
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    async def main():
        service = ChatService()
        await service.connect()
        
        try:
            # Test 1: Refinement Check
            print("\n--- Test 1: Prompt Refinement ---")
            query = "price of tcs"
            print(f"Original: {query}")
            
            response = await service.chat(
                message=query,
                user_id="test_user",
                session_id="test_session",
            )
            # We can't see the refined prompt directly from response but the log will show it
            print(f"Response: {response['content'][:200]}...")
            
        finally:
            await service.close()
    
    asyncio.run(main())
