from __future__ import annotations

from base import BaseModel
from .generation import Questions

class QuizDTO(BaseModel):
    questions: Questions
    course_code: str
    week_number: int    
