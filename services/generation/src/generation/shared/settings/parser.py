from __future__ import annotations

from base import BaseModel 
from .concept_card import ConceptCardExtractorSetting


class ParserSetting(BaseModel):
    upload_folder_path: str
    concept_card_extractor: ConceptCardExtractorSetting

