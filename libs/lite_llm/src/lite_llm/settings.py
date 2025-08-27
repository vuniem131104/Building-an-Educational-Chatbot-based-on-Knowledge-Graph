from __future__ import annotations

from base import BaseModel
from pydantic import HttpUrl
from pydantic import SecretStr


class LiteLLMSetting(BaseModel):
    url: HttpUrl
    token: SecretStr
    model: str
    frequency_penalty: float
    n: int
    temperature: float
    top_p: float
    max_completion_tokens: int
    dimension: int
    embedding_model: str
