from __future__ import annotations

from base import BaseModel
from pydantic import Field
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
    
class Topic(BaseModel):
    name: str = Field(..., description="The name of the topic")
    description: str = Field(..., description="A brief description of the topic")
    difficulty_level: str = Field(..., description="The difficulty level of the topic")
    estimated_right_answer_rate: float = Field(..., description="Estimated right answer rate for the topic")
    bloom_taxonomy_level: str = Field(..., description="Bloom's taxonomy level for the topic")
    
class QuizQuestion(BaseModel):
    question: str
    answer: str
    distractors: list[str]
    explanation: str
    topic: Topic
    week_number: int
    course_code: str