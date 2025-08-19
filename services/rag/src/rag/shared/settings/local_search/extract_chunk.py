from __future__ import annotations

from base import BaseModel


class ExtractChunkSetting(BaseModel):
    threshold: float
    top_k: int
