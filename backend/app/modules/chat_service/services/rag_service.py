from uuid import UUID
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.config.settings import settings


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) service using Qdrant.
    Retrieves relevant document chunks for context.
    """
    
    _embeddings: HuggingFaceEmbeddings | None = None
    _client: QdrantClient | None = None
    
    @classmethod
    def get_embeddings(cls) -> HuggingFaceEmbeddings:
        """Get or create embeddings model"""
        if cls._embeddings is None:
            cls._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        return cls._embeddings
    
    @classmethod
    def get_client(cls) -> QdrantClient:
        """Get or create Qdrant client"""
        if cls._client is None:
            cls._client = QdrantClient(url=settings.qdrant_url)
        return cls._client
    
    @classmethod
    def search(
        cls,
        collection_name: str,
        query: str,
        user_id: str | None = None,
        session_id: str | None = None,
        limit: int = 3,
    ) -> list[dict]:
        """
        Search for relevant chunks in Qdrant.
        
        Args:
            collection_name: Qdrant collection to search
            query: Search query
            user_id: Optional filter by user
            session_id: Optional filter by session
            limit: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        embeddings = cls.get_embeddings()
        
        # Build filter conditions
        filter_conditions = []
        if user_id:
            filter_conditions.append(
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            )
        if session_id:
            filter_conditions.append(
                FieldCondition(key="session_id", match=MatchValue(value=session_id))
            )
        
        query_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        try:
            vector_store = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                url=settings.qdrant_url,
                collection_name=collection_name,
            )
            
            results = vector_store.similarity_search(
                query,
                k=limit,
                filter=query_filter,
            )
            
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in results
            ]
        except Exception:
            # Collection might not exist
            return []
    
    @classmethod
    def search_all_session_sources(
        cls,
        query: str,
        user_id: str,
        session_id: str,
        collections: list[str],
        limit_per_collection: int = 2,
    ) -> list[dict]:
        """
        Search across all source collections for a session.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            session_id: Session ID for filtering
            collections: List of collection names to search
            limit_per_collection: Results per collection
            
        Returns:
            Combined list of relevant chunks from all sources
        """
        all_results = []
        
        for collection in collections:
            results = cls.search(
                collection_name=collection,
                query=query,
                user_id=user_id,
                session_id=session_id,
                limit=limit_per_collection,
            )
            all_results.extend(results)
        
        return all_results
