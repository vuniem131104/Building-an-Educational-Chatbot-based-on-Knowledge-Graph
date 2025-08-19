from __future__ import annotations

import pandas as pd
from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMEmbeddingInput
from lite_llm import LiteLLMService
from logger import get_logger
from graph_db import Neo4jService 
from rag.shared.settings.local_search import ExtractEntitySetting

from .cypher_query import SIMILARITY_GETTING


logger = get_logger(__name__)


class EntityExtracterInput(BaseModel):
    """
    Input model for entity extraction operations.
    Contains the text to extract entities from.
    """
    text: str = 'query_text'


class EntityExtracterOutput(BaseModel):
    """
    Output model for entity extraction results.
    Contains the extracted entities as a DataFrame and the embedding vector.
    """
    entities: pd.DataFrame
    embedded_query: list[float]


class EntityExtracter(BaseService):

    neo4j_service: Neo4jService
    litellm_service: LiteLLMService
    extract_entity_setting: ExtractEntitySetting

    async def process(self, input: EntityExtracterInput) -> EntityExtracterOutput:
        """
        Extract entities from input text using embedding and vector similarity search.

        Embeds the input text, retrieves similar entities from the Neo4j database using the embedding,
        and returns the results as a DataFrame along with the embedding vector.

        Args:
            input (EntityExtracterInput): The input containing the text to process.

        Returns:
            EntityExtracterOutput: The extracted entities (as a DataFrame) and the embedding vector.

        Raises:
            Exception: If embedding or entity retrieval fails.
        """
        try:
            embedded_query = await self.__embed_query(input.text)
            if not embedded_query:
                raise Exception('Could not extract entities from input')

            similar_entities = await self.__get_similar_entities(embedded_query)
            return EntityExtracterOutput(
                entities=similar_entities,
                embedded_query=embedded_query,
            )
        except Exception as e:
            logger.exception(
                f'Error while extracting entities: {e}',
                extra={
                    'input': input,
                },
            )
            raise e

    async def __embed_query(self, query: str) -> list | None:
        """
        Generate an embedding vector for the given query using the LLM embedding service.

        Args:
            query (str): The text to embed.

        Returns:
            list | None: The embedding vector, or None if embedding fails.
        """
        try:
            embedding_result = await self.litellm_service.embedding_llm_async(
                model=self.extract_entity_setting.embedding_model,
                inputs=query,
            )

            return embedding_result.embedding
        except Exception as e:
            logger.exception(
                f'Some error occurred while embedding query: {e}',
                extra={
                    'query': query,
                },
            )
            return None

    async def __get_similar_entities(self, input_vector: list[float]) -> pd.DataFrame:
        """
        Retrieve entities from Neo4j that are most similar to the input embedding vector.

        Args:
            input_vector (list[float]): The embedding vector to use for similarity search.

        Returns:
            pd.DataFrame: DataFrame of similar entities, chunk IDs, and similarity scores.

        Raises:
            Exception: If the output is not a DataFrame or retrieval fails.
        """
        try:
            results = await self.neo4j_service.execute_query(
                cypher=SIMILARITY_GETTING,
                parameters={
                    'index_name': self.extract_entity_setting.index_name,
                    'embedding': input_vector,
                    'k': self.extract_entity_setting.top_k,
                    'query_nodes': self.extract_entity_setting.query_nodes,
                },
                output_format='pandas',
            )
            return results
        except Exception as e:
            logger.exception(
                f'Error while getting similar entities: {e}',
                extra={
                    'input_vector': input_vector,
                },
            )
            raise e
