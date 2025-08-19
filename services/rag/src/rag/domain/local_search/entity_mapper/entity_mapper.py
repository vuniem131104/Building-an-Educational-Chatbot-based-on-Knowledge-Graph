from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import cast
from typing import LiteralString  # type: ignore

from base import BaseModel
from base import BaseService
from logger import get_logger
from graph_db import Neo4jService
from pandas import DataFrame
from rag.shared.settings.local_search import ExtractChunkSetting
from rag.shared.settings.local_search import ExtractRelationshipSetting

from .cypher_query import CONTEXT_MAPPER
from .cypher_query import TEXT_UNIT_MAPPING

logger = get_logger(__name__)


class EntityMapperInput(BaseModel):
    """
    Input model for entity mapping operations.
    Contains the entities DataFrame and the embedding vector for mapping.
    """
    entities: DataFrame
    embedded_query: list[float]


class EntityMapper(BaseService):

    neo4j_service: Neo4jService
    extract_chunk_settings: ExtractChunkSetting
    extract_relationship_settings: ExtractRelationshipSetting

    async def process(self, inputs: EntityMapperInput) -> list[dict] | None:
        """
        Map extracted entities to relevant text chunks and their context using Neo4j queries.

        This method maps entity chunk IDs to text units, then maps those to context using additional Neo4j queries.
        The result is post-processed into a list of dictionaries containing chunk, entities, relationships, and file names.

        Args:
            inputs (EntityMapperInput): Contains the entities DataFrame and the embedded query vector.

        Returns:
            list[dict] | None: List of context dictionaries for each chunk, or None if mapping fails.
        """

        # chunk_ids = inputs.entities['chunk_id'].tolist()
        
        # new_chunk_uids: list = []
        # for chunk_id in chunk_ids:
        #     new_chunk_uids.extend(chunk_id.split('_'))
        
        # logger.info(
        #     'HEHE',
        #     extra={
        #         'len': len(new_chunk_uids)
        #     }
        # )

        chunk_mapper = await self.__map_chunk(
            chunk_id=inputs.entities['chunk_id'].tolist(),
            embedded_query=inputs.embedded_query,
        )
        
        if not isinstance(chunk_mapper, DataFrame):
            logger.error(
                'Chunk mapping output is not a DataFrame',
            )
            return None
        if chunk_mapper.empty:
            logger.error(
                'Chunk mapping is empty',
            )
            return None

        context_mapper = await self.__map_contexts(
            inputs.entities['name'].tolist(),
            chunk_mapper['chunk_id'].tolist(),
            inputs.entities['description_id'].tolist(),
            inputs.embedded_query,
        )

        if not isinstance(context_mapper, DataFrame):
            logger.error(
                'Context mapping output is not a DataFrame',
            )
            return None

        if context_mapper.empty:
            logger.error(
                'Context mapping is empty',
            )
            return None

        try:
            context_mapper = self.__post_process_context(context_mapper.to_dict())
        except Exception as e:
            logger.exception(
                f'Error while post-processing context mapping: {e}',
            )
            return None
        return context_mapper

    async def __map_chunk(
        self,
        chunk_id: list[str],
        embedded_query: list[float],
    ) -> DataFrame | list[dict[str, Any]] | None:
        """
        Map chunk IDs to text units using a Neo4j query and the provided embedding vector.

        Args:
            chunk_id (list[str]): List of chunk IDs to map.
            embedded_query (list[float]): Embedding vector for similarity search.

        Returns:
            DataFrame | None: DataFrame of mapped text units, or None if mapping fails.
        """
        try:
            df = await self.neo4j_service.execute_query(
                cypher=TEXT_UNIT_MAPPING,
                parameters={
                    'chunk_ids': chunk_id,
                    'input_vector': embedded_query,
                    'threshold': self.extract_chunk_settings.threshold,
                    'k': self.extract_chunk_settings.top_k,
                },
                output_format='pandas',
            )

            return df

        except Exception as e:
            logger.exception(
                f'Error while mapping chunks for entity {chunk_id}: {e}',
            )
            return None

    async def __map_contexts(
        self,
        entity_names: list[str],
        chunk_ids: list[str],
        description_ids: list[str],
        embedded_query: list[float],
    ) -> DataFrame | list[dict[str, Any]] | None:
        """
        Map related entities and context from Neo4j using entity names, chunk IDs, and embedding vector.

        Args:
            entity_names (list[str]): Names of entities to map.
            chunk_ids (list[str]): Chunk IDs to use for mapping.
            description_ids (list[str]): Description IDs for mapping.
            embedded_query (list[float]): Embedding vector for similarity search.

        Returns:
            DataFrame | None: DataFrame of mapped related entities and context, or None if mapping fails.
        """
        try:
            df = await self.neo4j_service.execute_query(
                cypher=CONTEXT_MAPPER,
                parameters={
                    'entity_names': entity_names,
                    'chunk_uids': chunk_ids,
                    'description_ids': description_ids,
                    'input_vector': embedded_query,
                    'k': self.extract_relationship_settings.top_k,
                },
                output_format='pandas',
            )
            return df

        except Exception as e:
            logger.exception(
                f'Error while mapping related entities for entity {entity_names}: {e}',
            )
            return None

    def __post_process_context(self, context: dict) -> list:
        """
        Group and organize context data by chunk, aggregating entities, relationships, and file names.

        Args:
            context (dict): Dictionary with keys 'chunk', 'entity_description', 'relationship_descriptions', and 'file_name'.

        Returns:
            list: List of dictionaries, each with a chunk, unique entities, relationships, and file names.
        """
        grouped: dict = defaultdict(lambda: {'entities': [], 'relationships': [], 'file_name': []})

        for idx, chunk in context['chunk'].items():
            grouped[chunk]['entities'].append(context['entity_description'][idx])
            grouped[chunk]['relationships'].extend(context['relationship_descriptions'][idx])
            grouped[chunk]['file_name'].append(context['file_name'][idx])

        # Remove duplicates
        result = [
            {
                'chunk': chunk,
                'entities': list(set(values['entities'])),
                'relationships': list(set(values['relationships'])),
                'file_name': list(set(values['file_name'])),
            }
            for chunk, values in grouped.items()
        ]
        return result
