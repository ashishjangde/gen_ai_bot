"""
LLM Tools for LangGraph Agent

Tools available:
- Web Search (Tavily)
- Document Search (RAG)
- Memory Retrieval (STM/LTM)
- Calculator
- Date/Time
"""
from langchain_core.tools import tool
from tavily import TavilyClient
from datetime import datetime
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger("app.chat.tools")


# ============ Web Search Tool ============

@tool
def web_search(query: str) -> str:
    """
    Search the web for current information using Tavily.
    Use this when you need up-to-date information, news, or real-time data.
    
    Args:
        query: The search query to look up
        
    Returns:
        Relevant search results from the web with sources
    """
    if not settings.tavily_api_key:
        return "Web search is not configured. Please set TAVILY_API_KEY."
    
    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )
        
        results = []
        if response.get("answer"):
            results.append(f"**Summary:** {response['answer']}")
            results.append("")
        
        results.append("**Sources:**")
        for r in response.get("results", [])[:5]:
            results.append(f"- [{r['title']}]({r['url']})")
            results.append(f"  {r['content'][:200]}...")
            results.append("")
        
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Search failed: {str(e)}"


# ============ RAG / Document Search Tool ============

@tool
def search_documents(query: str, session_id: str, user_id: str) -> str:
    """
    Search through uploaded documents (PDFs, CSVs, web pages) for relevant information.
    Use this when the user asks about their uploaded files or documents.
    
    Args:
        query: The search query to find in documents
        session_id: The current chat session ID
        user_id: The current user ID
        
    Returns:
        Relevant excerpts from the user's uploaded documents
    """
    try:
        from app.modules.chat_service.services.rag_service import RAGService
        
        # Search across all collections for this session
        results = RAGService.search(
            query=query,
            user_id=user_id,
            session_id=session_id,
            k=5,
        )
        
        if not results:
            return "No relevant documents found. The user may not have uploaded any documents yet."
        
        # Format results
        formatted = ["**Found in documents:**\n"]
        for i, doc in enumerate(results, 1):
            content = doc.get("content", doc.get("page_content", ""))[:400]
            source = doc.get("metadata", {}).get("source", "Document")
            formatted.append(f"[{i}] ({source}): {content}...\n")
        
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return f"Document search failed: {str(e)}"


# ============ Memory Tools ============

@tool
def get_user_memory(query: str, user_id: str) -> str:
    """
    Retrieve long-term memories about the user - their preferences, facts, past interactions.
    Use this when you need to personalize responses or recall user-specific information.
    
    Args:
        query: What to search for in user's memory
        user_id: The user's ID
        
    Returns:
        Relevant memories and facts about the user
    """
    try:
        from app.modules.chat_service.services.memory_service import LongTermMemory
        
        memories = LongTermMemory.search_memories(user_id, query, limit=5)
        
        if not memories:
            return "No memories found for this user yet."
        
        formatted = ["**User memories:**\n"]
        for mem in memories:
            text = mem.get("memory", mem.get("text", ""))
            formatted.append(f"- {text}")
        
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}")
        return f"Memory retrieval failed: {str(e)}"


@tool 
def get_conversation_history(session_id: str) -> str:
    """
    Get recent conversation history from this chat session.
    Use this to recall what was discussed earlier in the conversation.
    
    Args:
        session_id: The current chat session ID
        
    Returns:
        Recent messages from this conversation
    """
    try:
        from app.modules.chat_service.services.memory_service import ShortTermMemory
        import asyncio
        
        # Run async function synchronously
        loop = asyncio.get_event_loop()
        messages = loop.run_until_complete(
            ShortTermMemory.get_session_messages(session_id)
        )
        
        if not messages:
            return "No previous messages in this conversation."
        
        formatted = ["**Recent conversation:**\n"]
        for msg in messages[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")[:200]
            formatted.append(f"**{role}:** {content}")
        
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        return f"History retrieval failed: {str(e)}"


# ============ Utility Tools ============

@tool
def get_current_datetime() -> str:
    """
    Get the current date and time.
    Use this when the user asks about the current time, date, or day.
    
    Returns:
        Current date and time in a readable format
    """
    now = datetime.now()
    return f"Current time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"


@tool
def calculate(expression: str) -> str:
    """
    Perform a mathematical calculation.
    Use this for arithmetic operations, unit conversions, or percentage calculations.
    
    Args:
        expression: A mathematical expression (e.g., "2 + 2", "sqrt(16)", "100 * 0.15")
        
    Returns:
        The result of the calculation
    """
    import math
    
    allowed_names = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow, "sqrt": math.sqrt,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "exp": math.exp,
        "pi": math.pi, "e": math.e,
    }
    
    try:
        expression = expression.replace("^", "**")
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"


@tool
def save_user_preference(user_id: str, fact: str) -> str:
    """
    Save an important fact or preference about the user for future reference.
    Use this when the user mentions something important about themselves.
    
    Args:
        user_id: The user's ID
        fact: The fact or preference to remember
        
    Returns:
        Confirmation that the memory was saved
    """
    try:
        from app.modules.chat_service.services.memory_service import LongTermMemory
        
        result = LongTermMemory.add_memory(user_id, fact)
        return "✓ I'll remember that!"
    except Exception as e:
        logger.error(f"Failed to save memory: {e}")
        return "I'll try to remember that."


# ============ Tool Collections ============

# Basic tools (always available)
BASIC_TOOLS = [
    get_current_datetime,
    calculate,
]

# Memory tools
MEMORY_TOOLS = [
    get_user_memory,
    get_conversation_history,
    save_user_preference,
]

# RAG tools
RAG_TOOLS = [
    search_documents,
]

# Web search
WEB_TOOLS = [
    web_search,
]

# All tools combined
ALL_TOOLS = BASIC_TOOLS + MEMORY_TOOLS + RAG_TOOLS + WEB_TOOLS


def get_tools(
    include_web_search: bool = False,
    include_rag: bool = True,
    include_memory: bool = True,
) -> list:
    """
    Get the list of tools to bind to the LLM.
    
    Args:
        include_web_search: Include Tavily web search
        include_rag: Include document search (RAG)
        include_memory: Include memory tools (STM/LTM)
        
    Returns:
        List of tools for the agent
    """
    tools = list(BASIC_TOOLS)  # Always include basic tools
    
    if include_memory:
        tools.extend(MEMORY_TOOLS)
    
    if include_rag:
        tools.extend(RAG_TOOLS)
    
    if include_web_search and settings.tavily_api_key:
        tools.extend(WEB_TOOLS)
    
    return tools
