from __future__ import annotations

from base import BaseModel

from .extract_chunk import ExtractChunkSetting
from .extract_entity import ExtractEntitySetting
from .extract_relationship import ExtractRelationshipSetting


class LocalSearchSettings(BaseModel):
    extract_chunk_settings: ExtractChunkSetting
    extract_entity_settings: ExtractEntitySetting
    extract_relationship_settings: ExtractRelationshipSetting
