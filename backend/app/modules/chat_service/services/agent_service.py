"""
LangGraph Agent - Autonomous Tool Selection

The agent automatically decides which tools to use based on the query.
No user configuration needed - just send a message.

Tools available:
- search_documents (RAG)
- get_user_memory (LTM)
- get_conversation_history (STM)
- save_user_preference
- web_search (real-time info)
- calculate
- get_current_datetime
"""
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.config.settings import settings
from app.config.logging import get_logger
from app.modules.chat_service.tools.llm_tools import get_tools

logger = get_logger("app.chat.agent")


# ============ State ============

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "Conversation messages"]
    user_id: str
    session_id: str


# ============ LLM ============

def get_llm():
    return ChatGroq(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0.7,
    )


# ============ Graph Nodes ============

def should_use_tools(state: AgentState) -> Literal["tools", "end"]:
    """Route based on whether agent wants to use tools"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def create_agent_node(tools: list):
    """Create agent node with all tools bound"""
    def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    return agent_node


# ============ Graph Builder ============

# Build graph once at module load (singleton pattern)
_TOOLS = get_tools(include_web_search=True, include_rag=True, include_memory=True)
_GRAPH = None


def get_agent_graph():
    """Get or create the agent graph (singleton)"""
    global _GRAPH
    
    if _GRAPH is None:
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", create_agent_node(_TOOLS))
        workflow.add_node("tools", ToolNode(_TOOLS))
        
        # Add edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            should_use_tools,
            {"tools": "tools", "end": END},
        )
        workflow.add_edge("tools", "agent")
        
        _GRAPH = workflow.compile()
    
    return _GRAPH


# ============ System Prompt ============

SYSTEM_PROMPT = """You are an intelligent AI assistant. You have access to tools - use them when helpful.

## Available Tools:
- **search_documents**: Search user's uploaded files (PDFs, CSVs). Use for document questions.
- **get_user_memory**: Recall facts about this user. Use to personalize responses.
- **save_user_preference**: Save important user facts for later.
- **web_search**: Search the internet. Use for current events, news, real-time data.
- **calculate**: Math calculations.
- **get_current_datetime**: Get current date/time.

## When to use tools:
- Questions about uploaded docs → search_documents
- "What's the latest..." / "Current news..." → web_search  
- Personal preferences / history → get_user_memory
- Math problems → calculate
- Time/date questions → get_current_datetime

## Guidelines:
- Use tools when they help, skip when not needed
- Be concise and cite sources
- Don't over-fetch - only use tools that directly help

Context: user_id={user_id}, session_id={session_id}
"""


# ============ Main Function ============

async def run_chat_agent(
    query: str,
    user_id: str,
    session_id: str,
    context_messages: list[dict] = None,
) -> tuple[str, list[dict]]:
    """
    Run the autonomous chat agent.
    
    Agent automatically decides:
    - Whether to search documents
    - Whether to check user memory
    - Whether to search the web
    - Whether to use calculator
    
    Args:
        query: User's message
        user_id: User ID (for tool context)
        session_id: Session ID (for tool context)
        context_messages: Recent conversation history
        
    Returns:
        (response_text, sources_used)
    """
    # Build system prompt
    system_content = SYSTEM_PROMPT.format(
        user_id=user_id,
        session_id=session_id,
    )
    
    # Build messages
    messages: list[BaseMessage] = [SystemMessage(content=system_content)]
    
    # Add conversation context (last 5 messages)
    if context_messages:
        for msg in context_messages[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    # Add current query
    messages.append(HumanMessage(content=query))
    
    # Get graph and run
    graph = get_agent_graph()
    
    initial_state: AgentState = {
        "messages": messages,
        "user_id": user_id,
        "session_id": session_id,
    }
    
    try:
        result = await graph.ainvoke(initial_state)
        
        # Extract response
        final_messages = result["messages"]
        response_text = ""
        sources = []
        
        # Get last AI message
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and msg.content:
                response_text = msg.content
                break
        
        # Track tools used
        tool_to_source = {
            "web_search": {"type": "web", "title": "Web Search"},
            "search_documents": {"type": "documents", "title": "Document Search"},
            "get_user_memory": {"type": "memory", "title": "User Memory"},
        }
        
        for msg in final_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "")
                    if name in tool_to_source:
                        sources.append(tool_to_source[name])
        
        return response_text, sources
        
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise
