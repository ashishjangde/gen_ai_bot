from mvp.app.config.settings import settings
from mvp.app.utils.vector_service import VectorService
import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages


logger = logging.getLogger(__name__)



class State(TypedDict):
    """State that flows through the graph."""
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    context: str  # Retrieved documents content


class ChatGraph:
    """
    A self-contained LangGraph chatbot.
    
    - Private nodes: _preprocess, _chatbot, _postprocess
    - Public method: run()
    
    Usage:
        from langchain_groq import ChatGroq
        
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        chat = ChatGraph(llm)
        
        response = await chat.run(
            message="Hello!",
            user_id="user_123",
            session_id="session_456"
        )
        print(response)
    """
    
    def __init__(
        self,
        llm: Any,
        system_prompt: str = "You are a helpful assistant.",
        fallback_message: str = "Sorry, something went wrong."
    ):
        """
        Args:
            llm: LangChain-compatible LLM (Groq, OpenAI, etc.)
            system_prompt: System message for the LLM
            fallback_message: Message if LLM fails
        """
        self.llm = llm
        self.system_prompt = system_prompt
        self.fallback_message = fallback_message
        self.vector_service = VectorService()  # Initialize vector service
        self._app = self._build_graph()
    
    # -------------------------------------------------------------------------
    # PRIVATE NODE: Preprocess
    # -------------------------------------------------------------------------
    async def _preprocess(self, state: State) -> dict:
        """Add system prompt to messages. (Placeholder, mostly)"""
        return {}  # System prompt injected in _chatbot using retrieved context is better

    # -------------------------------------------------------------------------
    # PRIVATE NODE: Retrieve (RAG)
    # -------------------------------------------------------------------------
    async def _retrieve(self, state: State) -> dict:
        """Fetch relevant documents for the user."""
        try:
            user_id = state.get("user_id")
            session_id = state.get("session_id")
            messages = state["messages"]
            
            if not messages:
                return {"context": ""}
                
            last_message = messages[-1].content
            if not isinstance(last_message, str):
                last_message = str(last_message)

            await self.vector_service.connect() # Ensure connection
            results = await self.vector_service.search(
                query=last_message,
                limit=3,
                user_id=user_id,
                # session_id=session_id  # Search user-wide docs, not just session-specific
            )
            # await self.vector_service.close() # Don't close here if we want potential reuse, or close if stateless.
            # Ideally VectorService should be persistent at app level.
            # For this tool, we connect/close or keep open. 
            # Let's keep open and rely on app shutdown to close? 
            # Or just close effectively.
            await self.vector_service.close()

            logger.info(f"Retrieval | user={user_id} | query='{last_message}' | found={len(results)}")

            if not results:
                return {"context": ""}
            
            # Format context
            context_text = "\n\n".join(
                [f"Source: {r['metadata'].get('filename', 'unknown')}\nContent: {r['content']}" for r in results]
            )
            return {"context": context_text}

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return {"context": ""}
    
    async def _chatbot(self, state: State) -> dict:
        """Call the LLM with context."""
        user_id = state.get("user_id", "unknown")
        context = state.get("context", "")
        
        try:
            # Construct System Prompt with Context
            final_system_prompt = self.system_prompt
            if context:
                final_system_prompt += f"\n\nRELEVANT CONTEXT (Use this to answer):\n{context}"
            
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=final_system_prompt)] + state["messages"]
            
            if hasattr(self.llm, "ainvoke"):
                response = await self.llm.ainvoke(messages)
            else:
                response = self.llm.invoke(messages)
            
            logger.info(f"LLM success | user={user_id}")
            return {"messages": [response]}
            
        except Exception as e:
            logger.error(f"LLM error | user={user_id} | {e}")
            return {"messages": [{"role": "assistant", "content": self.fallback_message}]}
    
    async def _postprocess(self, state: State) -> dict:
        """Log the response (add your logic here)."""
        messages = state["messages"]
        if messages:
            logger.debug(f"Response generated: {messages[-1]}")
        return {}  # No state changes
    
    def _build_graph(self):
        """Wire all nodes together."""
        graph = StateGraph(State)
        
        graph.add_node("preprocess", self._preprocess)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("chatbot", self._chatbot)
        graph.add_node("postprocess", self._postprocess)
        
        graph.add_edge(START, "preprocess")
        graph.add_edge("preprocess", "retrieve")
        graph.add_edge("retrieve", "chatbot")
        graph.add_edge("chatbot", "postprocess")
        graph.add_edge("postprocess", END)
        
        return graph.compile()
    

    async def run(self, message: str, user_id: str, session_id: str) -> str:
        """
        Run the chatbot with a user message.
        
        Args:
            message: The user's message
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            The assistant's response as a string
        """
        result = await self._app.ainvoke({
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "session_id": session_id
        })
        
        # Extract the last message content
        last_message = result["messages"][-1]
        if hasattr(last_message, "content"):
            return last_message.content
        return last_message.get("content", "")


# =============================================================================
# EXAMPLE
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Mock LLM that just echoes the context it sees
    class MockLLM:
        async def ainvoke(self, messages):
             # Find system message content to see if context was injected
            system_msg = next((m.content for m in messages if hasattr(m, "type") and m.type == "system" or (isinstance(m, dict) and m.get("role") == "system")), "")
            
            if "RELEVANT CONTEXT" in str(system_msg):
                return {"role": "assistant", "content": f"I found context! System Prompt length: {len(str(system_msg))}"}
            else:
                return {"role": "assistant", "content": "No context found in system prompt."}
    
    async def main():
        # Create the chat graph
        chat = ChatGraph(
            llm=MockLLM(),
            system_prompt="You are a friendly assistant."
        )
        
        # We need a user who HAS documents. 
        # Assuming 'user_123' has 'test.txt' from vector_service.py test run.
        print("\n--- Running Chat (User 123) ---")
        response = await chat.run(
            message="memory test", # Should match 'test.txt' content
            user_id="user_123", # Matches user_id from vector_service test
            session_id="session_456"
        )
        print(f"✅ Response: {response}")

        print("\n--- Running Chat (User 999 - No Context) ---")
        response_empty = await chat.run(
            message="memory test",
            user_id="user_999",
            session_id="session_456"
        )
        print(f"✅ Response: {response_empty}")
    
    asyncio.run(main())

