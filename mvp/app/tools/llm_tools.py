"""
Production-Ready LangGraph Chatbot
===================================

Architecture:
- One class (ChatGraph) contains everything
- Internal nodes are private (_methods)
- Only one public function exposed: run()

Flow: START → _preprocess → _chatbot → _postprocess → END
"""

from config.settings import settings
import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq


logger = logging.getLogger(__name__)


# =============================================================================
# STATE
# =============================================================================
class State(TypedDict):
    """State that flows through the graph."""
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=settings
)
class ChatGraph:
    """
    A self-contained LangGraph chatbot.
    
    - Private nodes: _preprocess, _chatbot, _postprocess
    - Public method: run()
    
    Usage:
        from langchain_groq import ChatGroq
        
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        chat = ChatGraph(llm)
        
        response = await chat.run(
            message="Hello!",
            user_id="user_123",
            session_id="session_456"
        )
        print(response)
    """
    
    def __init__(
        self,
        llm: Any,
        system_prompt: str = "You are a helpful assistant.",
        fallback_message: str = "Sorry, something went wrong."
    ):
        """
        Args:
            llm: LangChain-compatible LLM (Groq, OpenAI, etc.)
            system_prompt: System message for the LLM
            fallback_message: Message if LLM fails
        """
        self.llm = llm
        self.system_prompt = system_prompt
        self.fallback_message = fallback_message
        self._app = self._build_graph()
    
    # -------------------------------------------------------------------------
    # PRIVATE NODE: Preprocess
    # -------------------------------------------------------------------------
    async def _preprocess(self, state: State) -> dict:
        """Add system prompt to messages."""
        from langchain_core.messages import SystemMessage
        
        messages = state["messages"]
        
        # Check if first message is already a system message
        # Handle both dict and LangChain message objects
        if messages:
            first_msg = messages[0]
            is_system = (
                getattr(first_msg, "type", None) == "system" or
                (isinstance(first_msg, dict) and first_msg.get("role") == "system")
            )
            if is_system:
                return {}  # Already has system prompt
        
        # Add system prompt
        return {"messages": [SystemMessage(content=self.system_prompt)]}
    
    # -------------------------------------------------------------------------
    # PRIVATE NODE: Chatbot (calls LLM)
    # -------------------------------------------------------------------------
    async def _chatbot(self, state: State) -> dict:
        """Call the LLM and return response."""
        user_id = state.get("user_id", "unknown")
        
        try:
            messages = state["messages"]
            
            if hasattr(self.llm, "ainvoke"):
                response = await self.llm.ainvoke(messages)
            else:
                response = self.llm.invoke(messages)
            
            logger.info(f"LLM success | user={user_id}")
            return {"messages": [response]}
            
        except Exception as e:
            logger.error(f"LLM error | user={user_id} | {e}")
            return {"messages": [{"role": "assistant", "content": self.fallback_message}]}
    
    # -------------------------------------------------------------------------
    # PRIVATE NODE: Postprocess
    # -------------------------------------------------------------------------
    async def _postprocess(self, state: State) -> dict:
        """Log the response (add your logic here)."""
        messages = state["messages"]
        if messages:
            logger.debug(f"Response generated: {messages[-1]}")
        return {}  # No state changes
    
    # -------------------------------------------------------------------------
    # PRIVATE: Build the graph
    # -------------------------------------------------------------------------
    def _build_graph(self):
        """Wire all nodes together."""
        graph = StateGraph(State)
        
        # Add private nodes
        graph.add_node("preprocess", self._preprocess)
        graph.add_node("chatbot", self._chatbot)
        graph.add_node("postprocess", self._postprocess)
        
        # Define flow
        graph.add_edge(START, "preprocess")
        graph.add_edge("preprocess", "chatbot")
        graph.add_edge("chatbot", "postprocess")
        graph.add_edge("postprocess", END)
        
        return graph.compile()
    
    # -------------------------------------------------------------------------
    # PUBLIC: The only exposed function
    # -------------------------------------------------------------------------
    async def run(self, message: str, user_id: str, session_id: str) -> str:
        """
        Run the chatbot with a user message.
        
        Args:
            message: The user's message
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            The assistant's response as a string
        """
        result = await self._app.ainvoke({
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "session_id": session_id
        })
        
        # Extract the last message content
        last_message = result["messages"][-1]
        if hasattr(last_message, "content"):
            return last_message.content
        return last_message.get("content", "")


# =============================================================================
# EXAMPLE
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Mock LLM
    class MockLLM:
        async def ainvoke(self, messages):
            return {"role": "assistant", "content": "Hello! I'm here to help."}
    
    async def main():
        # Create the chat graph
        chat = ChatGraph(
            llm=MockLLM(),
            system_prompt="You are a friendly assistant."
        )
        
        # Use the ONE public function
        response = await chat.run(
            message="Hi there!",
            user_id="user_123",
            session_id="session_456"
        )
        
        print(f"\n✅ Response: {response}")
    
    asyncio.run(main())
