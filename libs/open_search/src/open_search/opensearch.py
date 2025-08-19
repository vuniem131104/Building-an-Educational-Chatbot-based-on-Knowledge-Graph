from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import Any

from base import BaseModel
from base import BaseService
from logger import get_logger
from opensearch_dsl import Document
from opensearchpy import OpenSearch

from .settings import OpenSearchSettings

logger = get_logger(__name__)


class SearchInput(BaseModel):
    index_name: str
    index_body: dict[str, Any] | None = None
    query: dict[str, Any]


class SearchOutput(BaseModel):
    results: list[dict]


class OpenSearchService(BaseService):
    settings: OpenSearchSettings

    @property
    def client(self) -> OpenSearch:
        """Create and return an OpenSearch client."""
        return OpenSearch(
            hosts=[{'host': self.settings.host, 'port': self.settings.port}],
            http_compress=True,  # enables gzip compression for request bodies
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    def index_exists(self, index_name: str) -> bool:
        """Check if an index exists in OpenSearch.

        Args:
            index_name (str): The name of the index to check.

        Returns:
            bool: True if the index exists, False otherwise.
        """
        return self.client.indices.exists(index=index_name)

    def create_index(self, index_name: str, index_body: dict[str, Any]) -> None:
        """Create an index in OpenSearch.

        Args:
            index_name (str): The name of the index to create.
            index_body (dict[str, Any]): The body of the index to create.
        """
        if not self.index_exists(index_name=index_name):
            response = self.client.indices.create(index=index_name, body=index_body)
            if response.get('acknowledged'):
                logger.debug(f"Index '{index_name}' created successfully.")
            else:
                logger.error(f"Failed to create index '{index_name}': {response}")
        else:
            logger.debug(f"Index '{index_name}' already exists. No action taken.")

    def delete_index(self, index_name: str) -> None:
        """
        Delete the specified index from OpenSearch.

        Args:
            index_name (str): The name of the index to delete.
        """
        if self.index_exists(index_name=index_name):
            response = self.client.indices.delete(index=index_name)
            if response.get('acknowledged'):
                logger.info(f"Index '{index_name}' deleted successfully.")
            else:
                logger.error(f"Failed to delete index '{index_name}': {response}")
        else:
            logger.warning(f"Index '{index_name}' does not exist. No action taken.")

    def add_documents(self, documents: list[Document], index_name: str) -> None:
        """
        Add documents to OpenSearch. Generic method that works with any Document type.

        Args:
            documents (list[Document]): A list of Document objects (Claim, MyDoc, etc.).
            index_name (str): The name of the index to add documents to.
        """
        if not documents:
            logger.warning('No documents provided to add.')
            return

        document_class = documents[0].__class__

        document_class.init(using=self.client)
        logger.debug(f'Initialized mapping for {document_class.__name__}')

        for document in documents:
            response = document.save(index=index_name, using=self.client)

            if response == 'created':
                logger.debug(
                    f"{document_class.__name__} document added to index '{index_name}'.",
                )
            else:
                logger.error(
                    f"Failed to add {document_class.__name__} document to index '{index_name}': {response}",
                )

    def delete_old_documents(self, index_name: str, days: int = 3) -> None:
        """
        Delete documents older than a specified number of days from the index.

        Args:
            index_name (str): The name of the index from which to delete old documents.
            days (int): The number of days to consider for deletion. Defaults to 3.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        query = {
            'query': {
                'range': {
                    'create_at': {
                        'lt': cutoff_timestamp,
                    },
                },
            },
        }

        try:
            response = self.client.delete_by_query(
                index=index_name,
                body=query,
                conflicts='proceed',
                scroll_size=1000,
                refresh=True,
            )
            logger.info(
                f"Deleted {response['deleted']} old documents from index '{index_name}'.",
            )
        except Exception as e:
            logger.error(f'Error deleting old documents: {e}')

    def process(self, inputs: SearchInput) -> SearchOutput:
        """
        Search for documents in the specified index.

        Args:
        query (str): The search query to execute.

        Returns:
        list[dict]: A list of documents that match the search query.
        """
        # check if the index exists
        self.create_index(
            index_name=inputs.index_name,
            index_body=inputs.index_body if inputs.index_body else {},
        )

        try:
            response = self.client.search(index=inputs.index_name, body=inputs.query)
            if response.get('hits', {}).get('hits'):
                results = [hit['_source'] for hit in response['hits']['hits']]
                logger.info(
                    f"Found {len(results)} documents in index '{inputs.index_name}'.",
                )
                return SearchOutput(results=results)
            else:
                logger.warning(f"No documents found in index '{inputs.index_name}'.")
                return SearchOutput(results=[])
        except Exception as e:
            logger.error(
                f"Error occurred while searching in index '{inputs.index_name}': {e}",
            )
            return SearchOutput(results=[])
