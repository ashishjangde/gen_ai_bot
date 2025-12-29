"""
Chat Service Tools

LangChain tools for the LangGraph agent:
- Web Search (Tavily)
- Document Search (RAG)  
- Memory Tools (STM/LTM)
- Utilities (Calculator, DateTime)
"""
from app.modules.chat_service.tools.llm_tools import (
    # Web
    web_search,
    # RAG
    search_documents,
    # Memory
    get_user_memory,
    get_conversation_history,
    save_user_preference,
    # Utilities
    get_current_datetime,
    calculate,
    # Collections
    get_tools,
    ALL_TOOLS,
    BASIC_TOOLS,
    MEMORY_TOOLS,
    RAG_TOOLS,
    WEB_TOOLS,
)
from app.modules.chat_service.tools.embedder import (
    load_pdf_to_qdrant,
    get_vector_store,
)

__all__ = [
    # Web Tools
    "web_search",
    # RAG Tools
    "search_documents",
    # Memory Tools
    "get_user_memory",
    "get_conversation_history", 
    "save_user_preference",
    # Utility Tools
    "get_current_datetime",
    "calculate",
    # Tool Collections
    "get_tools",
    "ALL_TOOLS",
    "BASIC_TOOLS",
    "MEMORY_TOOLS",
    "RAG_TOOLS",
    "WEB_TOOLS",
    # Embedder
    "load_pdf_to_qdrant",
    "get_vector_store",
]
