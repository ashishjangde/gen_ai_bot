

import logging
from typing import List, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models

from mvp.config.settings import settings
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

    async def ingest_file(self, file_key: str) -> bool:
        """
        Full pipeline: Download -> Chunk -> Embed -> Store.
        
        Args:
            file_key: S3 object key (e.g. 'folder/report.pdf')
        """
        try:
            # 1. Connect & Download
            await self.object_service.connect()
            file_bytes = await self.object_service.get(file_key)
            await self.object_service.close()
            
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

            await self.vector_store.aadd_documents(docs)
            
            logger.info(f"Ingested {file_key} ({len(docs)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Ingestion failed for {file_key}: {e}")
            return False

    async def search(self, query: str, limit: int = 5) -> List[dict]:
        """Semantic search."""
        try:
            results = await self.vector_store.asimilarity_search_with_score(query, k=limit)
            return [
                {"content": doc.page_content, "metadata": doc.metadata, "score": score}
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_file(self, file_key: str):
        """Delete all chunks for a specific file."""
        try:
            # Filter by source metadata
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.source",
                                match=models.MatchValue(value=file_key),
                            )
                        ]
                    )
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
    
    # Mock settings if running directly (or ensure env vars are set)
    # Ensure you have QDRANT_URL and QDRANT_API_KEY in .env
    
    async def main():
        service = VectorService()
        
        # 1. Ingest (Assume 'test.txt' exists in your bucket from previous steps)
        # You might need to run object_service.py test first to upload 'test.txt'
        print("\n--- Ingesting ---")
        success = await service.ingest_file("test.txt")
        print(f"Ingest: {'✅' if success else '❌'}")
        
        if success:
            # 2. Search
            print("\n--- Searching ---")
            results = await service.search("memory test")
            for r in results:
                print(f"[{r['score']:.2f}] {r['content'][:50]}...")
            
            # 3. Delete
            # await service.delete_file("test.txt")
            # print("\n--- Deleted ---")

    asyncio.run(main())
