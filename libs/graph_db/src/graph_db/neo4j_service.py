"""Neo4j Service for executing Cypher queries via official Neo4j driver."""

from __future__ import annotations

from neo4j import AsyncGraphDatabase
from typing import Dict, List, Any, Optional, Literal
from base import BaseModel
from .settings import Neo4jSetting
from logger import get_logger
from .utils import to_df
from pandas import DataFrame

logger = get_logger(__name__)



class Neo4jResult(BaseModel):
    """Result from Neo4j query execution."""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    rows_affected: int = 0


class Neo4jService(BaseModel):
    """Service for interacting with Neo4j database via official driver."""
    
    settings: Neo4jSetting
    
    @property
    def driver(self):
        return AsyncGraphDatabase.driver(
            self.settings.uri,
            auth=(self.settings.username, self.settings.password)
        )
    
    async def close(self):
        """Close the driver connection."""
        if self.driver:
            await self.driver.close()
    
    async def execute_query(
        self, 
        cypher: str, 
        parameters: Optional[Dict[str, Any]] = None,
        output_format: str | None = None,
    ) -> Neo4jResult | DataFrame:
        """
        Execute a single Cypher query using Neo4j driver.
        
        Args:
            cypher: The Cypher query to execute
            parameters: Optional parameters for the query
            
        Returns:
            Neo4jResult with success status and data/error
        """
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, parameters or {})
                
                if output_format == 'pandas':
                    return await to_df(result)
                
                # Get records and summary
                records = await result.data()
                summary = await result.consume()
                
                # Extract data in Neo4j format (list of records)
                data = []
                for record in records:
                    # Convert record to dict-like format
                    data.append(dict(record))
                
                # Calculate rows affected from counters
                counters = summary.counters
                rows_affected = (
                    counters.nodes_created + 
                    counters.relationships_created +
                    counters.nodes_deleted +
                    counters.relationships_deleted +
                    counters.properties_set
                )
                
                logger.info(f"Query executed successfully. Rows affected: {rows_affected}")
                return Neo4jResult(
                    success=True, 
                    data=data, 
                    rows_affected=rows_affected
                )
                
        except Exception as e:
            error_msg = f"Driver error: {str(e)}"
            logger.error(f"Neo4j driver error: {error_msg}")
            return Neo4jResult(success=False, error=error_msg)
    
    async def execute_queries(
        self, 
        queries: List[Dict[str, Any]]
    ) -> Neo4jResult:
        """
        Execute multiple Cypher queries in a single transaction using Neo4j driver.
        
        Args:
            queries: List of query dictionaries with 'statement' and optional 'parameters'
            
        Returns:
            Neo4jResult with success status and combined data/error
        """
        try:
            async with self.driver.session() as session:
                async def execute_transaction(tx):
                    all_data = []
                    total_rows_affected = 0
                    
                    for query in queries:
                        result = await tx.run(
                            query["statement"], 
                            query.get("parameters", {})
                        )
                        
                        # Get records and add to combined data
                        records = await result.data()
                        for record in records:
                            all_data.append(dict(record))
                        
                        # Get summary for counters
                        summary = await result.consume()
                        counters = summary.counters
                        total_rows_affected += (
                            counters.nodes_created + 
                            counters.relationships_created +
                            counters.nodes_deleted +
                            counters.relationships_deleted +
                            counters.properties_set
                        )
                    
                    return all_data, total_rows_affected
                
                # Execute in transaction
                all_data, total_rows_affected = await session.execute_write(execute_transaction)
                
                logger.info(f"Batch queries executed. Total rows affected: {total_rows_affected}")
                return Neo4jResult(
                    success=True, 
                    data=all_data, 
                    rows_affected=total_rows_affected
                )
                
        except Exception as e:
            error_msg = f"Batch driver error: {str(e)}"
            logger.error(f"Neo4j batch driver error: {error_msg}")
            return Neo4jResult(success=False, error=error_msg)
    
    async def health_check(self) -> bool:
        """
        Check if Neo4j is accessible and responsive.
        
        Returns:
            True if Neo4j is healthy, False otherwise
        """
        try:
            result = await self.execute_query("RETURN 1 as health")
            return result.success and len(result.data) > 0
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
    
    async def create_indexes(self) -> Neo4jResult:
        """
        Create common indexes for better performance.
        
        Returns:
            Neo4jResult indicating success/failure
        """
        index_queries = [
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:ORGANIZATION) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:PERSON) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:DOCUMENT) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:PROCEDURE) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:LOCATION) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:REQUIREMENT) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:FEE) ON (e.name)"},
            {"statement": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:TIMELINE) ON (e.name)"},
        ]
        
        return await self.execute_queries(index_queries)
