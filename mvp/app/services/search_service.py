"""
Search Service - Unified interface for Web Search (Tavily) and RAG (Qdrant)

Provides a clean abstraction over multiple search backends.
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

from tavily import TavilyClient

from mvp.app.config.settings import settings
from mvp.app.utils.vector_service import VectorService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result format."""
    content: str
    source: str  # URL or filename
    score: float = 0.0
    title: str = ""
    source_type: str = "unknown"  # 'web' or 'document'
    metadata: dict = field(default_factory=dict)


class SearchService:
    """
    Unified search interface for multiple backends.
    
    - Tavily: Real-time web search
    - Qdrant: RAG over user documents
    """
    
    def __init__(self):
        # Tavily client
        self._tavily: Optional[TavilyClient] = None
        
        # Qdrant VectorService
        self._vector_service: Optional[VectorService] = None
        
    # =========================================================================
    # Lifecycle
    # =========================================================================
    async def connect(self):
        """Initialize search backends."""
        # Tavily (sync client, but fast)
        if settings.tavily_api_key:
            self._tavily = TavilyClient(api_key=settings.tavily_api_key)
            logger.info("SearchService: Tavily connected")
        else:
            logger.warning("SearchService: Tavily API key not set, web search disabled")
        
        # VectorService for Qdrant
        self._vector_service = VectorService()
        await self._vector_service.connect()
        logger.info("SearchService: VectorService connected")
    
    async def close(self):
        """Close connections."""
        if self._vector_service:
            await self._vector_service.close()
            logger.info("SearchService: VectorService closed")
    
    # =========================================================================
    # Web Search (Tavily)
    # =========================================================================
    async def web_search(
        self,
        query: str,
        limit: int = 5,
        search_depth: str = "basic",  # 'basic' or 'advanced'
        include_answer: bool = True,
    ) -> list[SearchResult]:
        """
        Search the web using Tavily.
        
        Args:
            query: Search query
            limit: Max results
            search_depth: 'basic' (fast) or 'advanced' (comprehensive)
            include_answer: Include Tavily's AI-generated answer
            
        Returns:
            List of SearchResult objects
        """
        if not self._tavily:
            logger.warning("Tavily not configured, skipping web search")
            return []
        
        try:
            response = self._tavily.search(
                query=query,
                max_results=limit,
                search_depth=search_depth,
                include_answer=include_answer,
            )
            
            results = []
            
            # Include AI answer if available
            if include_answer and response.get("answer"):
                results.append(SearchResult(
                    content=response["answer"],
                    source="Tavily AI Summary",
                    score=1.0,
                    title="AI Summary",
                    source_type="web",
                ))
            
            # Include search results
            for item in response.get("results", []):
                results.append(SearchResult(
                    content=item.get("content", ""),
                    source=item.get("url", ""),
                    score=item.get("score", 0.0),
                    title=item.get("title", ""),
                    source_type="web",
                    metadata={"raw_content": item.get("raw_content", "")},
                ))
            
            logger.info(f"Web search: '{query[:30]}...' -> {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    # =========================================================================
    # RAG Search (Qdrant)
    # =========================================================================
    async def rag_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        """
        Search user documents in Qdrant.
        
        Args:
            query: Search query
            user_id: Filter by user (for multi-tenancy)
            session_id: Filter by session (optional)
            limit: Max results
            
        Returns:
            List of SearchResult objects
        """
        if not self._vector_service:
            logger.warning("VectorService not configured, skipping RAG search")
            return []
        
        try:
            raw_results = await self._vector_service.search(
                query=query,
                limit=limit,
                user_id=user_id,
                session_id=session_id,
            )
            
            results = []
            for item in raw_results:
                results.append(SearchResult(
                    content=item.get("content", ""),
                    source=item.get("metadata", {}).get("source", "unknown"),
                    score=item.get("score", 0.0),
                    title=item.get("metadata", {}).get("filename", "Document"),
                    source_type="document",
                    metadata=item.get("metadata", {}),
                ))
            
            logger.info(f"RAG search: '{query[:30]}...' | user={user_id} -> {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []
    
    # =========================================================================
    # Combined Search (for complex queries)
    # =========================================================================
    async def hybrid_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        web_limit: int = 3,
        rag_limit: int = 3,
    ) -> list[SearchResult]:
        """
        Search both web and documents, merge results.
        """
        web_results = await self.web_search(query, limit=web_limit)
        rag_results = await self.rag_search(query, user_id, session_id, limit=rag_limit)
        
        # Interleave results (RAG first for user context priority)
        combined = []
        for i in range(max(len(rag_results), len(web_results))):
            if i < len(rag_results):
                combined.append(rag_results[i])
            if i < len(web_results):
                combined.append(web_results[i])
        
        return combined


# =============================================================================
# Factory function for dependency injection
# =============================================================================
_search_service: Optional[SearchService] = None


async def get_search_service() -> SearchService:
    """Get or create the global SearchService instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
        await _search_service.connect()
    return _search_service
