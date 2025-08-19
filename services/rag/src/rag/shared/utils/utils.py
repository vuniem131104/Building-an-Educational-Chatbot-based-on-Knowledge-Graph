from __future__ import annotations

from functools import lru_cache

from rag.shared.settings import Settings

@lru_cache
def get_settings():
    return Settings() 