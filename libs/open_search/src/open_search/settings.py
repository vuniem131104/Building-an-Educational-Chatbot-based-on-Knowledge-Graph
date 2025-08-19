from __future__ import annotations

from base import BaseModel


class OpenSearchSettings(BaseModel):
    host: str
    port: int
    embedding_dimension: int
    index_name: str
    initial_admin_password: str
    number_of_shards: int
    number_of_replicas: int
    knn: bool
