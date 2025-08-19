from __future__ import annotations

from base import BaseModel
from enum import Enum 


class GenerationType(str, Enum):

    MULTIPLE_CHOICE = "multiple_choice"
    ESSAY = "essay"
    MIXED = "mixed"
    

class Question(BaseModel):
    question: str
    options: list[str] | None = None
    answer: str 
    explanation: str | None = None 
    level: str
    
    
class Questions(BaseModel):
    questions: list[Question]
    

class AssessmentType(str, Enum):
    QUIZ = "quiz"
    EXAM = "exam"
    
    
class GenerationBaseInput(BaseModel):
    generation_type: GenerationType
    num_questions: int
    num_multiple_choice: int | None = None
    num_essay: int | None = None
    course_code: str
    

class GenerationBaseOutput(BaseModel):
    questions: Questions
    course_code: str