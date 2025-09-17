"""Graph Builder Service - Tạo schema Document -> Chunk -> Entity -> Description cho Neo4j."""

from __future__ import annotations

import asyncio
import re
import uuid
from typing import List, Dict
from base import BaseModel
from base import BaseService
from logger import get_logger
from lite_llm import LiteLLMService, LiteLLMInput, CompletionMessage, Role, LiteLLMEmbeddingInput
from graph_db import Neo4jService
from indexing.domain.graph_builder.prompts import GRAPH_EXTRACTION_PROMPT

logger = get_logger(__name__)


# Prompt cho extraction

class BuilderInput(BaseModel):
    chunks: List[Dict[str, str]]
    document_file_name: str


class BuilderOutput(BaseModel):
    message: str
    entities_created: int
    relationships_created: int


class BuilderService(BaseService):
    """Service tạo knowledge graph theo schema Document -> Chunk -> Entity -> Description."""
    
    llm_service: LiteLLMService
    neo4j_service: Neo4jService
    
    async def process(self, input_data: BuilderInput) -> BuilderOutput:
        """Xử lý toàn bộ pipeline theo schema mới."""
        logger.info(f"Bắt đầu xử lý {len(input_data.chunks)} chunks cho document {input_data.document_file_name}")
        
        all_entities = []
        all_relationships = []
        
        # 1. Extract entities và relationships từ từng chunk
        for chunk in input_data.chunks:
            entities, relationships = await self._extract_from_chunk(
                chunk["chunk_id"], 
                chunk["chunk_text"]
            )
            all_entities.extend(entities)
            all_relationships.extend(relationships)
        
        logger.info(f"Đã extract {len(all_entities)} entities và {len(all_relationships)} relationships")
        
        # 2. Tạo Document node trước
        await self._create_document_node(input_data.document_file_name)
        
        # 3. Tạo schema với entities
        entities_created = await self._create_entities_with_schema(
            all_entities, input_data.document_file_name, input_data.chunks
        )
        
        # 4. Tạo relationships với schema
        relationships_created = await self._create_relationships_with_schema(all_relationships)
        
        return BuilderOutput(
            message=f"Thành công! Tạo {entities_created} entities và {relationships_created} relationships theo schema mới",
            entities_created=entities_created,
            relationships_created=relationships_created
        )
    
    async def _extract_from_chunk(self, chunk_id: str, chunk_text: str) -> tuple[List[Dict], List[Dict]]:
        """Extract entities và relationships từ một chunk bằng LLM."""
        try:
            # Gọi LLM để extract
            llm_input = LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.USER,
                        content=GRAPH_EXTRACTION_PROMPT.format(input_text=chunk_text)
                    )
                ],
            )
            
            response = await self.llm_service.process_async(llm_input)
            extracted_text = response.response
            
            print(extracted_text)
            
            # Parse kết quả
            entities = []
            relationships = []
            
            # Regex để tìm entities: [ENTITY]<|>name<|>type<|>description[/ENTITY]
            entity_pattern = r'\[ENTITY\]<\|>([^<|>]+)<\|>([^<|>]+)<\|>([^<|>]+?)\[/ENTITY\]'
            entity_matches = re.findall(entity_pattern, extracted_text, re.DOTALL)
            
            for match in entity_matches:
                entities.append({
                    'chunk_id': chunk_id,
                    'entity_name': match[0].strip(),
                    'entity_type': match[1].strip().lower(),  # lowercase type
                    'entity_description': match[2].strip()
                })
            
            # Regex để tìm relationships: [RELATIONSHIP]<|>source<|>target<|>relation<|>description[/RELATIONSHIP]
            rel_pattern = r'\[RELATIONSHIP\]<\|>([^<|>]+)<\|>([^<|>]+)<\|>([^<|>]+)<\|>([^<|>]+?)\[/RELATIONSHIP\]'
            rel_matches = re.findall(rel_pattern, extracted_text, re.DOTALL)
            
            for match in rel_matches:
                relationships.append({
                    'chunk_id': chunk_id,
                    'source_entity': match[0].strip(),
                    'target_entity': match[1].strip(),
                    'relationship': match[2].strip().lower(),  # lowercase type
                    'relationship_description': match[3].strip()
                })
            
            logger.info(f"Chunk {chunk_id}: {len(entities)} entities, {len(relationships)} relationships")
            return entities, relationships
            
        except Exception as e:
            logger.error(f"Lỗi extract chunk {chunk_id}: {e}")
            return [], []
    
    async def _create_document_node(self, file_name: str) -> bool:
        """Tạo Document node với thuộc tính file_name và uid."""
        try:
            document_uid = str(uuid.uuid4())
            
            cypher = f"""
            MERGE (doc:Document {{file_name: '{file_name}'}})
            SET doc.uid = '{document_uid}',
                doc.created_at = datetime()
            """
            
            result = await self.neo4j_service.execute_query(cypher)
            if result.success:
                logger.info(f"Tạo Document node thành công: {file_name} (uid: {document_uid})")
                return True
            else:
                logger.error(f"Lỗi tạo Document node: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi tạo Document node: {e}")
            return False
    
    async def _create_entities_with_schema(self, entities: List[Dict], document_file_name: str, chunks: List[Dict]) -> int:
        """Tạo entities theo schema mới với các thuộc tính đầy đủ và embedding."""
        if not entities:
            return 0
            
        # Tạo mapping chunk_id -> chunk_text
        chunk_texts = {chunk["chunk_id"]: chunk["chunk_text"] for chunk in chunks}
        
        # Tạo mapping chunk_id -> chunk_uid (mỗi chunk_id chỉ có 1 chunk_uid duy nhất)
        chunk_uids = {}
        chunk_embeddings = {}
        
        # Tạo embedding cho mỗi chunk text
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            chunk_text = chunk["chunk_text"]
            chunk_uids[chunk_id] = str(uuid.uuid4())
            
            # Tạo embedding cho chunk text
            embedding_result = await self.llm_service.embedding_llm_async(
                inputs=LiteLLMEmbeddingInput(
                    text=chunk_text,
                )
            )
            chunk_embeddings[chunk_id] = embedding_result.embedding
        
        created_count = 0
        
        for entity in entities:
            try:
                # Generate UIDs
                entity_uid = str(uuid.uuid4())
                desc_uid = str(uuid.uuid4())
                
                # Get chunk_uid and embedding from mapping
                chunk_id = entity['chunk_id']
                chunk_uid = chunk_uids[chunk_id]
                chunk_embedding = chunk_embeddings[chunk_id]
                
                # Escape quotes
                name = entity['entity_name'].replace("'", "\\'").replace('"', '\\"')
                description = entity['entity_description'].replace("'", "\\'").replace('"', '\\"')
                entity_type = entity['entity_type']
                chunk_text = chunk_texts.get(chunk_id, "Unknown chunk text").replace("'", "\\'").replace('"', '\\"')

                # Tạo embedding cho entity description
                desc_embedding_result = await self.llm_service.embedding_llm_async(
                    inputs=LiteLLMEmbeddingInput(
                        text=entity['entity_description'],
                    )
                )
                desc_embedding = desc_embedding_result.embedding

                # Tạo theo schema mới với chunk và description có embedding
                cypher = f"""
                // Tìm Document
                MATCH (doc:Document {{file_name: '{document_file_name}'}})
                
                // Tạo hoặc tìm Chunk theo uid với embedding
                MERGE (chunk:Chunk {{uid: '{chunk_uid}'}})
                ON CREATE SET chunk.text = '{chunk_text}',
                              chunk.embedding = {chunk_embedding}

                // Tạo Entity với name (unique), type (lowercase), uid
                MERGE (entity:Entity {{name: '{name}'}})
                SET entity.type = '{entity_type}',
                    entity.uid = '{entity_uid}'
                
                // Tạo Description cho Entity với embedding
                MERGE (desc:Description {{uid: '{desc_uid}'}})
                SET desc.chunk_uid = '{chunk_uid}',
                    desc.text = '{description}',
                    desc.type = 'ENTITY',
                    desc.embedding = {desc_embedding}
                
                // Tạo relationships theo schema
                MERGE (doc)-[:CONTAINED]->(chunk)
                MERGE (chunk)-[:MENTIONED]->(entity)
                MERGE (entity)-[:DESCRIBED]->(desc)      
                """

                result = await self.neo4j_service.execute_query(cypher)

                if result.success:
                    created_count += 1
                    logger.debug(f"Tạo entity với schema: {name} (type: {entity_type})")
                else:
                    logger.error(f"Lỗi tạo entity {name}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Lỗi xử lý entity {entity.get('entity_name', 'unknown')}: {e}")
        
        logger.info(f"Đã tạo {created_count}/{len(entities)} entities với schema và embedding")
        return created_count
    
    async def _create_relationships_with_schema(self, relationships: List[Dict]) -> int:
        """Tạo relationships với schema mới và Description nodes với embedding."""
        if not relationships:
            return 0
            
        created_count = 0
        
        for rel in relationships:
            try:
                # Generate UIDs
                relationship_uid = str(uuid.uuid4())
                desc_uid = str(uuid.uuid4())
                
                # Get chunk_id to find the correct chunk_uid
                chunk_id = rel['chunk_id']
                
                # Escape quotes
                source = rel['source_entity'].replace("'", "\\'").replace('"', '\\"')
                target = rel['target_entity'].replace("'", "\\'").replace('"', '\\"')
                rel_type = rel['relationship']
                description = rel['relationship_description'].replace("'", "\\'").replace('"', '\\"')
                
                # Tạo embedding cho relationship description
                desc_embedding_result = await self.llm_service.embedding_llm_async(
                    inputs=LiteLLMEmbeddingInput(
                        text=rel['relationship_description'],
                    )
                )
                desc_embedding = desc_embedding_result.embedding
                
                # Tạo schema: Entity -> RELATED -> Relationship -> RELATED -> Entity và Relationship -> DESCRIBED -> Description
                cypher = f"""
                // Tìm source và target entities
                MATCH (source:Entity {{name: '{source}'}})
                MATCH (target:Entity {{name: '{target}'}})
                
                // Tìm Chunk node để lấy uid của nó
                MATCH (chunk:Chunk)-[:MENTIONED]->(source)
                WITH source, target, chunk.uid as chunk_uid
                
                // Tạo Relationship node chỉ có uid
                MERGE (relationship:Relationship {{uid: '{relationship_uid}'}})
                
                // Tạo Description cho relationship với chunk_uid và embedding
                MERGE (desc:Description {{uid: '{desc_uid}'}})
                SET desc.chunk_uid = chunk_uid,
                    desc.text = '{description}',
                    desc.type = 'RELATIONSHIP',
                    desc.embedding = {desc_embedding}
                
                // Tạo schema relationships
                MERGE (source)-[:RELATED]->(relationship)
                MERGE (relationship)-[:RELATED]->(target)
                MERGE (relationship)-[:DESCRIBED]->(desc)
                """
                
                result = await self.neo4j_service.execute_query(cypher)
                
                if result.success:
                    created_count += 1
                    logger.debug(f"Tạo relationship schema: {source} -> {rel_type} -> {target}")
                else:
                    logger.error(f"Lỗi tạo relationship {source} -> {target}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Lỗi xử lý relationship {rel.get('source_entity', 'unknown')} -> {rel.get('target_entity', 'unknown')}: {e}")
        
        logger.info(f"Đã tạo {created_count}/{len(relationships)} relationships với schema và embedding")
        return created_count


# Test function với schema mới
async def test_service():
    """Test service với schema Document -> Chunk -> Entity -> Description."""
    from lite_llm import LiteLLMService, LiteLLMSetting
    from graph_db import Neo4jSetting, Neo4jService
    from pydantic import SecretStr, HttpUrl
    from uuid import uuid4
    
    # Tạo LiteLLM service
    litellm = LiteLLMService(
        litellm_setting=LiteLLMSetting(
            url=HttpUrl("http://localhost:9510"),
            token=SecretStr("abc123"),
            model="gemini-2.5-flash",
            frequency_penalty=0.0,
            n=1,
            temperature=0.0,
            top_p=1.0,
            max_completion_tokens=10000,
            dimension=1536,
            embedding_model="gemini-embedding"
        )
    )
    
    # Dùng Neo4jService thật
    neo4j_service = Neo4jService(
        settings=Neo4jSetting(
            uri="bolt://localhost:17687",
            username="neo4j",
            password="4_Kz1pLYqtmVsxFJED_gxTN8rBcu4oQKAEqw9mm6zUHY"
        )
    )
    
    service = BuilderService(
        llm_service=litellm,
        neo4j_service=neo4j_service
    )
    
    test_input = BuilderInput(
        document_file_name="Lecture2_General Concepts for ML.pdf",
        chunks=[
            {
                "chunk_id": str(uuid4()),
                "chunk_text": """**Lecture2_General Concepts for ML.pdf**

# Slide 53: Khung học thống kê

Slide này trình bày định nghĩa chính thức về đầu ra của người học trong Khung học thống kê (Statistical Learning Framework).

**Định nghĩa chính thức về đầu ra của người học:**

*   **Quy tắc dự đoán (A prediction rule) $h$:**
    $h: \mathcal{X} \to \mathcal{Y} \quad (1)$
    *   $h$ là một bộ phân loại (classifier), bộ dự đoán (predictor), giả thuyết (hypothesis) hoặc hàm ánh xạ (mapping function).
    *   Ví dụ: $h$ có thể là hàm tuyến tính với ngưỡng (thresholding) như đã học trong bài trước.

*   **Thuật toán học (Learning algorithm) $A$:**
    *   Cho một thuật toán $A$, chúng ta ký hiệu $A(S)$ là tập hợp các bộ phân loại/giả thuyết được tạo ra bằng cách áp dụng $A$ trên tập dữ liệu $S$.
    *   $h$ có thể tổng quát hơn định nghĩa của một hàm.
    *   Một ví dụ là $h$ là hàm ngẫu nhiên (stochastic function).

---

# Slide 54: Khung học thống kê

Slide này mô tả một quy trình tạo dữ liệu đơn giản trong Khung học thống kê (Statistical Learning Framework) và các ghi chú quan trọng.

**Quy trình tạo dữ liệu đơn giản:**

*   **Giả định 1:** Chúng ta có một phân phối xác suất $D$ trên $\mathcal{X}$.
*   **Giả định 2:** Cho $D$, chúng ta lấy một mẫu $x_i \sim D$.
*   **Giả định 3:** Chúng ta có một hàm nhãn "đúng" (correct label function) $c$:
    $c: \mathcal{X} \to \mathcal{Y} \quad (2)$
    Sao cho $y_i = c(x_i)$, và tập dữ liệu $S = \{(x_1, y_1), ..., (x_m, y_m)\}$.

**Ghi chú:**

1.  $c$ là hàm mà chúng ta muốn khôi phục. Tuy nhiên, chúng ta không biết $D$ và $c$. Thuật toán học $"""
            }
        ]
    )
    
    result = await service.process(test_input)
    print(f"Kết quả: {result.message}")
    
    # Check Neo4j health
    health = await neo4j_service.health_check()
    print(f"Neo4j health: {health}")
    
    return result


if __name__ == "__main__":
    
    # Chạy test với schema mới
    asyncio.run(test_service())
