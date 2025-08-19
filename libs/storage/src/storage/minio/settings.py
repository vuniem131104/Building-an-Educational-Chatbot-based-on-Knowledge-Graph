from __future__ import annotations

from base import BaseModel


class MinioSetting(BaseModel):
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool