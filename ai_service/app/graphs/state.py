from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class GenerationGraphState(TypedDict):
    """
    State structure for the Generation Mode LangGraph.
    This state is passed between nodes and persisted to PostgreSQL.
    """
    session_id: str
    user_id: str
    topic: str
    total_days: int
    time_per_day: str
    lesson_plan: Optional[Dict[str, Any]]
    current_day: int
    chat_history: List[BaseMessage]
