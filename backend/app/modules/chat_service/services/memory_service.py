import json
from uuid import UUID
from typing import Any
from app.config.valkey import get_valkey_client
from app.config.settings import settings
from mem0 import Memory


class ShortTermMemory:
    """
    Short-Term Memory using Valkey (Redis-compatible).
    Stores last N messages per session with TTL.
    """
    
    PREFIX = "stm:"
    MAX_MESSAGES = 10
    TTL_SECONDS = 3600  # 1 hour
    
    @classmethod
    async def get_session_messages(cls, session_id: UUID) -> list[dict[str, str]]:
        """Get recent messages for a session"""
        client = await get_valkey_client()
        key = f"{cls.PREFIX}{session_id}"
        
        messages_json = await client.lrange(key, 0, cls.MAX_MESSAGES - 1)
        messages = [json.loads(m) for m in messages_json]
        
        return messages
    
    @classmethod
    async def add_message(cls, session_id: UUID, role: str, content: str) -> None:
        """Add a message to session's short-term memory"""
        client = await get_valkey_client()
        key = f"{cls.PREFIX}{session_id}"
        
        message = json.dumps({"role": role, "content": content})
        
        # Push to left (newest first)
        await client.lpush(key, message)
        
        # Trim to max messages
        await client.ltrim(key, 0, cls.MAX_MESSAGES - 1)
        
        # Reset TTL
        await client.expire(key, cls.TTL_SECONDS)
    
    @classmethod
    async def clear_session(cls, session_id: UUID) -> None:
        """Clear all messages for a session"""
        client = await get_valkey_client()
        key = f"{cls.PREFIX}{session_id}"
        await client.delete(key)


class LongTermMemory:
    """
    Long-Term Memory using Mem0.
    Stores user facts, preferences, and key insights.
    """
    
    _memory: Any = None
    
    @classmethod
    def get_memory(cls) -> Any:
        """Get or create Mem0 memory instance"""
        if not MEM0_AVAILABLE:
            return None
            
        if cls._memory is None:
            if settings.mem0_api_key:
                cls._memory = Memory(api_key=settings.mem0_api_key)
            else:
                # Local storage mode
                cls._memory = Memory()
        
        return cls._memory
    
    @classmethod
    def add_memory(cls, user_id: str, content: str, metadata: dict | None = None) -> dict | None:
        """Add a memory for a user"""
        memory = cls.get_memory()
        if memory is None:
            return None
            
        return memory.add(
            content,
            user_id=user_id,
            metadata=metadata or {}
        )
    
    @classmethod
    def search_memories(cls, user_id: str, query: str, limit: int = 5) -> list[dict]:
        """Search user's memories"""
        memory = cls.get_memory()
        if memory is None:
            return []
            
        results = memory.search(query, user_id=user_id, limit=limit)
        return results.get("results", []) if isinstance(results, dict) else results
    
    @classmethod
    def get_all_memories(cls, user_id: str) -> list[dict]:
        """Get all memories for a user"""
        memory = cls.get_memory()
        if memory is None:
            return []
            
        results = memory.get_all(user_id=user_id)
        return results.get("results", []) if isinstance(results, dict) else results


class MemoryService:
    """Combined memory service for chat context"""
    
    @classmethod
    async def get_context(cls, user_id: UUID, session_id: UUID, query: str) -> dict:
        """
        Get combined memory context for prompt construction.
        Returns STM messages and LTM facts.
        """
        # Get short-term memory (recent messages)
        stm_messages = await ShortTermMemory.get_session_messages(session_id)
        
        # Get long-term memory (user facts relevant to query)
        ltm_facts = LongTermMemory.search_memories(str(user_id), query, limit=5)
        
        return {
            "stm": stm_messages,
            "ltm": [fact.get("memory", fact.get("text", "")) for fact in ltm_facts],
        }
    
    @classmethod
    async def update_stm(cls, session_id: UUID, role: str, content: str) -> None:
        """Update short-term memory with new message"""
        await ShortTermMemory.add_message(session_id, role, content)
    
    @classmethod
    def extract_to_ltm(cls, user_id: str, content: str) -> None:
        """Extract and store facts to long-term memory (called async via RQ)"""
        LongTermMemory.add_memory(user_id, content)
