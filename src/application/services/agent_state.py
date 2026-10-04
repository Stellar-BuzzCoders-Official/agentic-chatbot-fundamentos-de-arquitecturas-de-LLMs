from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    rejected: bool
    request_handoff: bool
    violence_count: int
    prompt_injection_count: int
    evasion_count: int
    repetitive_count: int
