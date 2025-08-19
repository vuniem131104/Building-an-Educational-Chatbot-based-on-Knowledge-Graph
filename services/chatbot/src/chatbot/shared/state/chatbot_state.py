from typing import Dict, TypedDict
from typing import Any 

class ChatbotState(TypedDict):
    raw_question: str 
    rephrased_question: str
    sub_questions: list[str]
    conversation_history: list[dict[str, Any]]
    refined_contexts: list[str]
    need_rag: bool
    answer: str
    references: list[str]
    detected_fields: Dict[str, str]
    filled_profile_info: Dict[str, Any]