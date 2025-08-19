from __future__ import annotations

from base import BaseModel

class LectureInfo(BaseModel):
    title: str
    introduction: str
    lecture_learning_outcomes: list[str]
    materials: list[str]
    
class CourseExtractorSetting(BaseModel):
    upload_folder_path: str
    model: str 
    temperature: float
    top_p: float
    n: int
    frequency_penalty: float
    max_completion_tokens: int