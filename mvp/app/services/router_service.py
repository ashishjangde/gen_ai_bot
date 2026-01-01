"""
Router Service - Intelligent intent classification using low-cost LLM
router_service.py

Analyzes user messages and determines which tool/action to take.
Uses a cheap, fast model (e.g., llama-3.2-3b-preview) for efficiency.
"""

import logging
from typing import Literal
from enum import Enum

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from mvp.app.config.settings import settings

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """Possible intents for routing."""
    WEB_SEARCH = "web_search"        # Need real-time info from internet
    RAG_SEARCH = "rag_search"        # Need info from user's documents
    FINANCIAL_DATA = "financial_data"  # Stock prices, market data
    MEMORY_RECALL = "memory_recall"  # Need to recall user preferences/facts
    DIRECT_ANSWER = "direct_answer"  # Can answer without external tools


ROUTER_SYSTEM_PROMPT = """You are an intent classifier for a ChatGPT-like assistant.

Your job is to analyze the user's message and determine what action is needed.
You can select MULTIPLE intents if needed, separated by commas.
Available intents:

- web_search: User needs current/real-time information from the internet
  Examples: "What's the weather today?", "Latest news about AI", "Who won the game yesterday?"

- rag_search: User is asking about content from their uploaded documents/files
  Examples: "What does my PDF say about X?", "Summarize the document I uploaded", "Find in my files..."
  NOTE: Use this intent if the user asks "from the file", "from the pdf", or asks specifically about uploaded content.

- financial_data: User is asking for stock prices, market data, or financial information for a specific company/ticker.
  Examples: "Price of TCS", "How is Apple stock doing?", "Tesla stock price", "Market cap of Nvidia"

- memory_recall: User is referencing their preferences, past conversations, or personal facts
  Examples: "Remember I told you...", "What's my favorite...?", "You said earlier that...", "What is my name?", "Who am I?"
  NOTE: Use this intent if the user asks personal questions about themselves or past context.

- direct_answer: General knowledge, greetings, or questions you can answer without external tools
  Examples: "Hello", "What is Python?", "Explain quantum physics", "Write a poem"

Consider the conversation history and available context when making your decision.

Do not over-trigger tools. Only select multiple if distinctly required.
Respond with the intent keyword(s), separated by comma, nothing else."""


class RouterService:
    """
    Intelligent router that classifies user intent.
    
    Uses a low-cost, fast LLM to analyze messages and determine
    which tool/action path to take in the agent graph.
    """
    
    def __init__(self, model_name: str = None):
        """
        Args:
            model_name: Groq model for analysis (default: llama-3.2-3b-preview)
        """
        self.model_name = model_name or settings.analyzer_model or "llama-3.3-70b-versatile"
        self._llm = None
    
    def connect(self):
        """Initialize the analyzer LLM."""
        self._llm = ChatGroq(
            model=self.model_name,
            api_key=settings.llm_api_key,
            temperature=0,  # Deterministic for classification
            max_tokens=20,  # Only need one word
        )
        logger.info(f"RouterService: Using model {self.model_name}")
    
    async def classify(
        self,
        message: str,
        history: list[dict] = None,
        has_files: bool = False,
    ) -> list[str]:
        """
        Classify user intent.
        Returns a list of intent strings (e.g. ['web_search', 'financial_data'])
        """
        """
        Classify user intent.
        
        Args:
            message: Current user message
            history: Recent conversation history (optional)
            has_files: Whether the user has uploaded files in this session
            
        Returns:
            Intent enum value
        """
        if not self._llm:
            self.connect()
        
        # Heuristic: Force MEMORY_RECALL for obvious personal questions
        msg_lower = message.lower()
        if any(phrase in msg_lower for phrase in ["my name", "who am i", "what did i say", "do you remember", "my favorite"]):
             logger.info(f"Router: Heuristic override -> MEMORY_RECALL")
             logger.info(f"Router: Heuristic override -> MEMORY_RECALL")
             return [Intent.MEMORY_RECALL.value]
        
        # Build messages for LLM
        system_msg = ROUTER_SYSTEM_PROMPT
        if has_files:
            system_msg += "\n\nCONTEXT: User HAS uploaded files/documents for this session."
        else:
            system_msg += "\n\nCONTEXT: User has NOT uploaded any files (do not choose rag_search unless user explicitly asks to check files)."
            
        messages = [SystemMessage(content=system_msg)]
        
        # Add recent history for context
        if history:
            # Only include last 3 messages for efficiency
            for msg in history[-3:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=f"[Previous] {content}"))
        
        # Current message
        messages.append(HumanMessage(content=f"[Current] {message}"))
        
        try:
            response = await self._llm.ainvoke(messages)
            raw_response = response.content.strip().lower()
            
            # Split by comma
            parts = [p.strip() for p in raw_response.split(",")]
            
            detected_intents = []
            
            for part in parts:
                if "web_search" in part: detected_intents.append(Intent.WEB_SEARCH.value)
                elif "rag_search" in part: detected_intents.append(Intent.RAG_SEARCH.value)
                elif "financial_data" in part: detected_intents.append(Intent.FINANCIAL_DATA.value)
                elif "memory_recall" in part: detected_intents.append(Intent.MEMORY_RECALL.value)
            
            # Default to direct answer if empty
            if not detected_intents:
                # Fallback logic
                if not has_files and "file" not in message.lower() and "pdf" not in message.lower():
                     detected_intents.append(Intent.DIRECT_ANSWER.value)
                elif "rag_search" in raw_response:
                     # Fallback specific check
                     detected_intents.append(Intent.RAG_SEARCH.value)
            
            # Unique
            detected_intents = list(set(detected_intents))
            
            logger.info(f"Router: '{message[:30]}...' -> {detected_intents}")
            return detected_intents
            
        except Exception as e:
            logger.error(f"Router classification error: {e}")
            return [Intent.DIRECT_ANSWER.value]
            
        except Exception as e:
            logger.error(f"Router classification error: {e}")
            # Default to direct answer on error
            return Intent.DIRECT_ANSWER
    
    async def classify_with_confidence(
        self,
        message: str,
        history: list[dict] = None,
    ) -> tuple[Intent, float]:
        """
        Classify with confidence score (for future use).
        Currently returns 1.0 confidence.
        """
        intent = await self.classify(message, history)
        return intent, 1.0


# =============================================================================
# Factory function for dependency injection
# =============================================================================
_router_service: RouterService = None


def get_router_service() -> RouterService:
    """Get or create the global RouterService instance."""
    global _router_service
    if _router_service is None:
        _router_service = RouterService()
        _router_service.connect()
    return _router_service
