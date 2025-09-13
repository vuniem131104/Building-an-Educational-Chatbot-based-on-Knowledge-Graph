from __future__ import annotations

from base import BaseModel


class QuestionAnswerGeneratorSetting(BaseModel):
    model: str
    temperature: float
    top_p: float
    n: int
    frequency_penalty: float
    max_completion_tokens: int
    reasoning_effort: str | None = None
    collection_name: str