from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages



def merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dictionaries. Used for Reducer."""
    if not left: left = {}
    if not right: right = {}
    return {**left, **right}

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    intent: list[str]
    tool_results: Annotated[dict, merge_dicts]
    stm_history: list[dict]
    ltm_history: list[dict]
    has_files: bool
    refined_prompt: str
    summary: str

