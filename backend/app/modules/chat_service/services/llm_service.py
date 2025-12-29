from typing import AsyncGenerator
from groq import Groq
from openai import OpenAI
from app.config.settings import settings


class LLMService:
    """
    LLM service for generating chat responses.
    Supports Groq, OpenAI, and other OpenAI-compatible APIs.
    """
    
    _client: Groq | OpenAI | None = None
    
    @classmethod
    def get_client(cls) -> Groq | OpenAI:
        """Get or create LLM client"""
        if cls._client is None:
            if settings.llm_provider == "groq":
                cls._client = Groq(api_key=settings.llm_api_key)
            else:
                cls._client = OpenAI(api_key=settings.llm_api_key)
        return cls._client
    
    @classmethod
    def build_prompt(
        cls,
        query: str,
        stm_messages: list[dict],
        ltm_facts: list[str],
        rag_context: list[dict],
    ) -> list[dict]:
        """
        Build optimized prompt with memory context.
        
        Structure:
        1. System prompt with LTM facts
        2. RAG context (document chunks)
        3. STM messages (recent conversation)
        4. User query
        """
        messages = []
        
        # System prompt with LTM facts
        system_content = "You are a helpful AI assistant. Be concise and accurate."
        
        if ltm_facts:
            facts_text = "\n".join(f"- {fact}" for fact in ltm_facts[:5])
            system_content += f"\n\nUser context:\n{facts_text}"
        
        if rag_context:
            sources_text = "\n\n".join(
                f"[Source {i+1}]: {chunk['content'][:500]}"
                for i, chunk in enumerate(rag_context[:3])
            )
            system_content += f"\n\nRelevant documents:\n{sources_text}"
            system_content += "\n\nUse the above documents to answer when relevant. Cite sources."
        
        messages.append({"role": "system", "content": system_content})
        
        # Add STM messages (recent conversation) in chronological order
        for msg in reversed(stm_messages[-5:]):  # Last 5 messages
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages
    
    @classmethod
    def generate(cls, messages: list[dict]) -> str:
        """Generate a non-streaming response"""
        client = cls.get_client()
        
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        
        return response.choices[0].message.content or ""
    
    @classmethod
    async def generate_stream(cls, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Generate a streaming response"""
        client = cls.get_client()
        
        stream = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
