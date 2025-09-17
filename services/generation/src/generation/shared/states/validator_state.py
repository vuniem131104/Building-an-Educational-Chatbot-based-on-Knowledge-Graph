from typing import TypedDict
from generation.shared.models import QuizQuestion

class ValidatorState(TypedDict):
    quiz_question: QuizQuestion
    factual_message: str
    factual_score: int
    pedagogical_message: str
    pedagogical_score: int
    psychometric_message: str
    psychometric_score: int
    score: int
    feedback: str
    