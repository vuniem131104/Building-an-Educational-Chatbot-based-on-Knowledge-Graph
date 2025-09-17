from __future__ import annotations

from base import BaseModel


class ExtractEntitySetting(BaseModel):
    index_name: str
    top_k: int
    query_nodes: int
    dimensions: int = 1536
