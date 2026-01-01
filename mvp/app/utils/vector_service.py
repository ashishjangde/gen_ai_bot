import logging
from typing import List, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models
from mvp.app.config.settings import settings
from mvp.app.utils.object_service import ObjectService
from mvp.app.utils.doc_processor import DocProcessor

logger = logging.getLogger(__name__)


class VectorService:
    """
    High-level service for RAG operations.
    Combines ObjectService, DocProcessor, and Qdrant.
    """

    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        
        # 1. Services
        self.object_service = ObjectService(bucket=settings.supabase_bucket_name)
        self.doc_processor = DocProcessor()
        
        # 2. Embeddings (The Chef)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # 3. Vector Database (The Vault)
        self._client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        
        # Ensure collection exists
        if not self._client.collection_exists(collection_name):
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created collection '{collection_name}'")

        self.vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
            embedding=self.embeddings,
        )

    async def connect(self):
        """Startup: connect to object storage."""
        await self.object_service.connect()
        logger.info("VectorService connected")

    async def close(self):
        """Shutdown: close object storage connection."""
        await self.object_service.close()
        logger.info("VectorService closed")

    async def add_texts(self, texts: List[str], metadatas: List[dict]) -> bool:
        """
        Directly add texts to vector store.
        """
        try:
            await self.vector_store.aadd_texts(texts=texts, metadatas=metadatas)
            logger.info(f"Added {len(texts)} texts to {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add texts: {e}")
            return False

    async def ingest_file(self, file_key: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> bool:
        """
        Full pipeline: Download -> Chunk -> Embed -> Store.
        
        Args:
            file_key: S3 object key (e.g. 'folder/report.pdf')
            user_id: Optional owner ID.
            session_id: Optional session ID (e.g. for ephemeral chat files).
        """
        try:
            # 1. Download (assumes persistent connection)
            file_bytes = await self.object_service.get(file_key)
            
            if not file_bytes:
                logger.error(f"File not found: {file_key}")
                return False

            # 2. Chunk
            file_ext = file_key.split(".")[-1]
            docs = await self.doc_processor.process(file_bytes, file_ext)
            
            if not docs:
                logger.warning(f"No text extracted from {file_key}")
                return False
                
            # 3. Add Metadata
            for doc in docs:
                doc.metadata["source"] = file_key
                doc.metadata["filename"] = file_key.split("/")[-1]
                if user_id:
                    doc.metadata["user_id"] = user_id
                if session_id:
                    doc.metadata["session_id"] = session_id

            await self.vector_store.aadd_documents(docs)
            
            logger.info(f"Ingested {file_key} ({len(docs)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Ingestion failed for {file_key}: {e}")
            return False

    async def search(self, query: str, limit: int = 5, user_id: Optional[str] = None, session_id: Optional[str] = None) -> List[dict]:
        """Semantic search with optional filtering."""
        try:
            filter_conditions = []
            if user_id:
                filter_conditions.append(
                    models.FieldCondition(key="metadata.user_id", match=models.MatchValue(value=user_id))
                )
            if session_id:
                filter_conditions.append(
                    models.FieldCondition(key="metadata.session_id", match=models.MatchValue(value=session_id))
                )
            
            qdrant_filter = models.Filter(must=filter_conditions) if filter_conditions else None
            
            # Use similarity_search_with_score which accepts filter in kargs or distinct arg depending on implementation
            # LangChain Qdrant accepts 'filter' argument
            results = await self.vector_store.asimilarity_search_with_score(
                query, 
                k=limit,
                filter=qdrant_filter
            )
            
            return [
                {"content": doc.page_content, "metadata": doc.metadata, "score": score}
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_file(self, file_key: str, user_id: Optional[str] = None):
        """Delete all chunks for a specific file (optionally restricted by user_id)."""
        try:
            must_cards = [
                models.FieldCondition(key="metadata.source", match=models.MatchValue(value=file_key))
            ]
            if user_id:
                must_cards.append(
                    models.FieldCondition(key="metadata.user_id", match=models.MatchValue(value=user_id))
                )

            self._client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(must=must_cards)
                ),
            )
            logger.info(f"Deleted vectors for {file_key}")
            return True
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            return False


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        service = VectorService()
        await service.connect()
        
        try:
            # 1. Ingest with user_id
            print("\n--- Ingesting ---")
            success = await service.ingest_file("test.txt", user_id="user_123")
            print(f"Ingest: {'✅' if success else '❌'}")
            
            if success:
                print("\n--- Searching (User 123) ---")
                results = await service.search("memory test", user_id="user_123")
                print(f"Found: {len(results)} docs")
                for r in results:
                    print(f"[{r['score']:.2f}] {r['content'][:50]}...")

                # 3. Search (Wrong User)
                print("\n--- Searching (User 999) ---")
                results_wrong = await service.search("memory test", user_id="user_999")
                print(f"Found: {len(results_wrong)} docs (Expected: 0)")

                # 4. Search (No Filter - Admin mode)
                print("\n--- Searching (No Filter) ---")
                results_all = await service.search("memory test")
                print(f"Found: {len(results_all)} docs")
                
                # 5. Delete (Restricted)
                # await service.delete_file("test.txt", user_id="user_123")
                # print("\n--- Deleted ---")

        finally:
            await service.close()

    asyncio.run(main())


