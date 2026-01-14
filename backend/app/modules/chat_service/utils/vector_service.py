from typing import List, Optional
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
import logging
from langchain_qdrant import QdrantVectorStore
from app.modules.chat_service.utils.doc_processor import DocProcessor
from app.modules.utils.object_service import ObjectService
from qdrant_client import QdrantClient , models
from app.config.settings import settings


logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name,
        self.object_service : ObjectService = ObjectService(),
        self.doc_processor : DocProcessor = DocProcessor()
        self.embedder : HuggingFaceEmbeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self._client = QdrantClient(
            url=settings.qdrant_url
        )
        if not self._client.collection_exists(self.collection_name):
            self._client.create_collection(
                self.collection_name,
                distance=models.Distance.COSINE,
                vector_size=384,
            )
        logger.info(f"Collection '{self.collection_name}' created")

        self.vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=self.collection_name,
            embedding=self.embedder,
        )
    
    async def connect(self):
        await self.object_service.connect()
        logger.info("VectorService connected")
    
    async def close(self):
        await self.object_service.close()
        logger.info("VectorService closed")
    
    async def add_texts(self, texts: List[str], metadatas: List[dict]) -> bool:
        try:
            await self.vector_store.aadd_texts(texts=texts, metadatas=metadatas)
            logger.info(f"Added {len(texts)} texts to {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add texts: {e}")
            return False
    
    async def ingest_file(self, file_key: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> bool:
        try:
            file_bytes = await self.object_service.get_bytes(file_key)
            if not file_bytes:
                logger.error(f"File not found: {file_key}")
                return False
            file_ext = file_key.split(".")[-1]
            docs = await self.doc_processor.process(file_bytes, file_ext)
            if not docs:
                logger.warning(f"No text extracted from {file_key}")
                return False
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
                filter=models.Filter(must=must_cards)
            )
            logger.info(f"Deleted {file_key} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
