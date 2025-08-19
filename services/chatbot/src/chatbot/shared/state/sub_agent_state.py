from typing import TypedDict

class SubAgentState(TypedDict):
    sub_question: str
    raw_context: str
    refined_context: str
    references: list[str]