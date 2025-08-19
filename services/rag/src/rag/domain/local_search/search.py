from __future__ import annotations

import pandas as pd
from lite_llm import LiteLLMService
from graph_db import Neo4jService
from rag.domain.local_search.entity_extracter import EntityExtracter
from rag.domain.local_search.entity_extracter import EntityExtracterInput
from rag.shared.settings.local_search import LocalSearchSettings
from logger import get_logger
from base import BaseModel
from base import BaseService

from .entity_mapper import EntityMapper
from .entity_mapper import EntityMapperInput

logger = get_logger(__name__)


class LocalSearchInput(BaseModel):
    input_text: str


class LocalSearchOutput(BaseModel):
    chunk_df: list


class LocalSearch(BaseService):
    neo4j_service: Neo4jService
    litellm_service: LiteLLMService
    local_search_settings: LocalSearchSettings

    @property
    def entity_extracter(self) -> EntityExtracter:
        return EntityExtracter(
            neo4j_service=self.neo4j_service,
            litellm_service=self.litellm_service,
            extract_entity_setting=self.local_search_settings.extract_entity_settings,
        )

    @property
    def entity_mapper(self) -> EntityMapper:
        return EntityMapper(
            neo4j_service=self.neo4j_service,
            extract_chunk_settings=self.local_search_settings.extract_chunk_settings,
            extract_relationship_settings=self.local_search_settings.extract_relationship_settings,
        )

    async def process(self, inputs: LocalSearchInput) -> LocalSearchOutput:
        """
        Process input text using local entity extraction and mapping to generate a structured search output.

        Extracts entities from the input, maps them to relevant document chunks and context, and returns the result.
        If no relevant information is found, returns an empty output.

        Args:
            inputs (LocalSearchInput): The input containing the text to process.

        Returns:
            LocalSearchOutput: Output with mapped context, completion time, LLM calls, and prompt tokens.
        """
        # Step 1: Extract entities
        extracted_entities, embedded_query = await self._extract_entities(
            inputs.input_text,
        )

        # Step 2: Map entities
        mapped_data = await self.entity_mapper.process(
            EntityMapperInput(
                entities=extracted_entities,
                embedded_query=embedded_query,
            ),
        )
        if not mapped_data:
            logger.error(
                'Not found information on documents in database',
            )
            return LocalSearchOutput(
                chunk_df=[],
            )

        return LocalSearchOutput(
            chunk_df=mapped_data,
        )

    async def _extract_entities(
        self,
        input_text: str,
    ) -> tuple[pd.DataFrame, list[float]]:
        """
        Extract entities and their embedding from the input text.

        Args:
            input_text (str): The text to extract entities from.

        Returns:
            tuple[pd.DataFrame, list[float]]: Filtered entities DataFrame and the embedding vector for the input.
        """
        extracted_output = [
            await self.entity_extracter.process(
                input=EntityExtracterInput(text=input_text),
            ),
        ]

        extracted_entities = pd.concat([e.entities for e in extracted_output])
        
        extracted_entities = (
            extracted_entities.drop_duplicates(subset=['description_id'])
            .sort_values('score', ascending=False)
            .reset_index()
        )

        embedded_query = extracted_output[0].embedded_query

        return extracted_entities, embedded_query
