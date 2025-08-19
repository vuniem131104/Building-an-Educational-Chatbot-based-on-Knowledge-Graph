from __future__ import annotations

SIMILARITY_GETTING = """CALL db.index.vector.queryNodes($index_name, $query_nodes, $embedding)
YIELD node, score WHERE node.type = 'ENTITY'
MATCH (node)<-[:DESCRIBED]-(e:Entity)
RETURN e.name AS name, e.type AS type, node.uid AS description_id, node.text AS description, node.chunk_uid AS chunk_id, score ORDER BY score DESC limit $k
"""
