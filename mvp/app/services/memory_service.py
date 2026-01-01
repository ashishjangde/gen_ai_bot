"""
Memory Service - Unified interface for STM (Valkey) and LTM (Mem0)

STM (Short-Term Memory): Sliding window of recent conversation via Valkey
LTM (Long-Term Memory): Persistent user facts/preferences via Mem0
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass

from mem0 import Memory
import valkey.asyncio as valkey

from mvp.app.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Unified memory entry format."""
    content: str
    role: str  # 'user' or 'assistant'
    metadata: dict = None


class MemoryService:
    """
    Manages both short-term (Valkey) and long-term (Mem0) memory.
    
    STM: Sliding window cache for conversation context (fast, ephemeral)
    LTM: Persistent storage for user preferences/facts (slower, persistent)
    """
    
    def __init__(
        self,
        stm_ttl: int = 3600,  # 1 hour TTL for STM
        stm_max_messages: int = 20,  # Max messages in sliding window
    ):
        self.stm_ttl = stm_ttl
        self.stm_max_messages = stm_max_messages
        
        # Valkey client (async)
        self._valkey: Optional[valkey.Valkey] = None
        
        # Mem0 client (sync, but we'll wrap in async)
        self._mem0: Optional[Memory] = None
        
    # =========================================================================
    # Lifecycle
    # =========================================================================
    async def connect(self):
        """Initialize connections to Valkey and Mem0."""
        # Valkey (STM)
        self._valkey = valkey.from_url(
            settings.valkey_url,
            decode_responses=True
        )
        logger.info("MemoryService: Valkey connected")
        
        # Mem0 (LTM) - using cloud API
        # Mem0 is sync but lightweight, we'll use it directly
        if settings.mem0_api_key:
            self._mem0 = Memory.from_config({
                "llm": {
                    "provider": "groq",
                    "config": {
                        "model": "llama-3.1-8b-instant",
                        "api_key": settings.llm_api_key,
                    }
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2"
                    }
                },
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "url": settings.qdrant_url,
                        "api_key": settings.qdrant_api_key or None,
                        "collection_name": "mem0_memories"
                    }
                }
            })
            logger.info("MemoryService: Mem0 initialized")
        else:
            logger.warning("MemoryService: Mem0 API key not set, LTM disabled")
    
    async def close(self):
        """Close connections."""
        if self._valkey:
            await self._valkey.close()
            logger.info("MemoryService: Valkey closed")
    
    # =========================================================================
    # STM: Short-Term Memory (Valkey)
    # =========================================================================
    def _stm_key(self, session_id: str) -> str:
        """Generate Valkey key for session."""
        return f"stm:{session_id}"
    
    async def get_stm(self, session_id: str, limit: Optional[int] = None) -> list[dict]:
        """
        Get recent messages from sliding window.
        
        Returns list of messages: [{"role": "user", "content": "..."}, ...]
        """
        if not self._valkey:
            return []
        
        limit = limit or self.stm_max_messages
        key = self._stm_key(session_id)
        
        try:
            # Get last N messages (stored as JSON strings)
            raw_messages = await self._valkey.lrange(key, -limit, -1)
            messages = [json.loads(m) for m in raw_messages]
            return messages
        except Exception as e:
            logger.error(f"STM get error: {e}")
            return []
    
    async def add_stm(self, session_id: str, role: str, content: str):
        """
        Add a message to the sliding window.
        Automatically trims to max_messages.
        """
        if not self._valkey:
            return
        
        key = self._stm_key(session_id)
        message = json.dumps({"role": role, "content": content})
        
        try:
            # Push to right (newest at end)
            await self._valkey.rpush(key, message)
            
            # Trim to keep only last N messages
            await self._valkey.ltrim(key, -self.stm_max_messages, -1)
            
            # Refresh TTL
            await self._valkey.expire(key, self.stm_ttl)
            
        except Exception as e:
            logger.error(f"STM add error: {e}")
    
    async def clear_stm(self, session_id: str):
        """Clear session's STM."""
        if not self._valkey:
            return
        
        key = self._stm_key(session_id)
        await self._valkey.delete(key)
        
    def _summary_key(self, session_id: str) -> str:
        """Generate Valkey key for session summary."""
        return f"stm:summary:{session_id}"
        
    async def get_summary(self, session_id: str) -> Optional[str]:
        """Get the current conversation summary."""
        if not self._valkey:
            return None
        return await self._valkey.get(self._summary_key(session_id))
        
    async def set_summary(self, session_id: str, summary: str):
        """Update conversation summary."""
        if not self._valkey:
            return
        
        key = self._summary_key(session_id)
        await self._valkey.set(key, summary, ex=self.stm_ttl)
    
    # =========================================================================
    # LTM: Long-Term Memory (Mem0)
    # =========================================================================
    async def get_ltm(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        """
        Search long-term memory for relevant facts about the user.
        
        Returns: [{"memory": "User prefers dark mode", "score": 0.9}, ...]
        """
        if not self._mem0:
            return []
        
        try:
            # Mem0 search is sync, but fast enough for our use case
            results = self._mem0.search(query, user_id=user_id, limit=limit)
            return results.get("results", [])
        except Exception as e:
            logger.error(f"LTM search error: {e}")
            return []
    
    async def add_ltm(self, user_id: str, content: str, metadata: dict = None):
        """
        Add a fact to long-term memory.
        Mem0 will automatically extract and deduplicate facts.
        """
        if not self._mem0:
            return
        
        try:
            messages = [{"role": "user", "content": content}]
            self._mem0.add(messages, user_id=user_id, metadata=metadata)
            logger.info(f"LTM added for user {user_id}")
        except Exception as e:
            logger.error(f"LTM add error: {e}")
    
    async def get_all_ltm(self, user_id: str) -> list[dict]:
        """Get all memories for a user."""
        if not self._mem0:
            return []
        
        try:
            results = self._mem0.get_all(user_id=user_id)
            return results.get("results", [])
        except Exception as e:
            logger.error(f"LTM get_all error: {e}")
            return []


# =============================================================================
# Factory function for dependency injection
# =============================================================================
_memory_service: Optional[MemoryService] = None


async def get_memory_service() -> MemoryService:
    """Get or create the global MemoryService instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
        await _memory_service.connect()
    return _memory_service
