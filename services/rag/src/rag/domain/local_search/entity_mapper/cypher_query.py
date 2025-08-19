from __future__ import annotations


TEXT_UNIT_MAPPING = """MATCH (c: Chunk)
WHERE c.uid IN $chunk_ids
WITH c, gds.similarity.cosine(c.embedding, $input_vector) AS similarity_score
WHERE similarity_score > $threshold
RETURN c.uid AS chunk_id, c.text AS text, similarity_score
ORDER BY similarity_score DESC LIMIT $k
"""

CONTEXT_MAPPER = """
MATCH (e:Entity)-[rel]-(c:Chunk)
WHERE c.uid IN $chunk_uids AND e.name IN $entity_names

OPTIONAL MATCH (e)-[:RELATED]-(r)-[:DESCRIBED]->(d)
WHERE d.embedding IS NOT NULL AND d.chunk_uid IN $chunk_uids

OPTIONAL MATCH (e)-[:DESCRIBED]->(d2)
WHERE d2.uid IN $description_ids AND d2.embedding IS NOT NULL

OPTIONAL MATCH (d3)-[:CONTAINED]->(c)

WITH
  e, c, d, d2, d3,
  CASE
    WHEN d IS NOT NULL THEN gds.similarity.cosine(d.embedding, $input_vector)
    WHEN d2 IS NOT NULL THEN gds.similarity.cosine(d2.embedding, $input_vector)
    ELSE 0.0
  END AS similarity_score

RETURN
    e.name AS entity_name,
    c.text AS chunk,
    d2.text AS entity_description,
    COLLECT(DISTINCT d.text) AS relationship_descriptions,
    d3.file_name AS file_name,
    similarity_score
ORDER BY similarity_score DESC
LIMIT $k
"""
