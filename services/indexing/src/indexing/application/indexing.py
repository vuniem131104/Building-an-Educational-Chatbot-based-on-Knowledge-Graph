from typing import Any
from base import BaseModel 
from base import BaseApplication 
from fastapi import Request
from uuid import uuid4
from indexing.domain.parser import ParserInput 
from indexing.domain.parser import ParserService 
from indexing.domain.chunker import ChunkerInput 
from indexing.domain.chunker import ChunkerService
from indexing.domain.graph_builder import BuilderInput 
from indexing.domain.graph_builder import BuilderService
from indexing.celery_app import celery_app


from logger import get_logger


logger = get_logger(__name__)

class IndexingApplicationInput(BaseModel):
    """Input for the indexing application."""
    file_name: str
    

class IndexingApplicationOutput(BaseModel):
    pass 


class IndexingApplication(BaseApplication):
    
    request: Any  # Allow any type, not just Request
    
    class Config:
        arbitrary_types_allowed = True
    
    @staticmethod
    @celery_app.task(name="tasks.index_file", bind=True)
    def index_file_async(self, file_name: str):
        """Celery task để xử lý indexing file async"""
        try:
            # Tạo mock request với services
            mock_request = IndexingApplication._create_mock_request()
            
            # Chạy indexing
            app = IndexingApplication(request=mock_request)
            
            import asyncio
            result = asyncio.run(
                app.run(IndexingApplicationInput(file_name=file_name))
            )
            
            logger.info(
                'Celery indexing task completed',
                extra={'file_name': file_name, 'task_id': self.request.id}
            )
            
            return {
                "status": "success",
                "file_name": file_name,
                "task_id": self.request.id
            }
            
        except Exception as e:
            logger.exception(
                'Celery indexing task failed',
                extra={'file_name': file_name, 'task_id': self.request.id, 'error': str(e)}
            )
            raise self.retry(countdown=60, max_retries=3)
    
    @staticmethod
    def _create_mock_request():
        """Tạo mock request với state giống FastAPI app"""
        from indexing.shared.utils import get_settings
        from lite_llm import LiteLLMService
        from storage.minio import MinioService
        from graph_db import Neo4jService
        
        settings = get_settings()
        
        class MockState:
            def __init__(self):
                self.settings = settings
                self.litellm_service = LiteLLMService(litellm_setting=settings.litellm)
                self.minio_service = MinioService(settings=settings.minio)
                self.neo4j_service = Neo4jService(settings=settings.neo4j)
        
        class MockApp:
            def __init__(self):
                self.state = MockState()
        
        class MockRequest:
            def __init__(self):
                self.app = MockApp()
        
        return MockRequest()
    
    @property
    def parser(self) -> ParserService:
        return ParserService(
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service, 
            settings=self.request.app.state.settings.parser,
        )
        
    @property
    def chunker(self) -> ChunkerService:
        return ChunkerService(
            chunker_setting=self.request.app.state.settings.chunker,
        )
        
    @property
    def builder(self) -> BuilderService:
        return BuilderService(
            llm_service=self.request.app.state.litellm_service,
            neo4j_service=self.request.app.state.neo4j_service,
        )
        
    async def run(self, inputs: IndexingApplicationInput) -> IndexingApplicationOutput:
        try:
            logger.info(
                'Starting Parser Service',
                extra={
                    'file_name': inputs.file_name
                }
            )
            parser_output = await self.parser.process(
                ParserInput(
                    file_name=inputs.file_name
                )
            )
            logger.info(
                'Parser Service completed',
                extra={
                    'file_name': inputs.file_name
                }
            )
        except Exception as e:
            logger.exception(
                'Parser Service failed',
                extra={
                    'file_name': inputs.file_name,
                    'error': str(e)
                }
            )
            
        try:
            logger.info(
                'Starting Chunker Service',
                extra={
                    'file_name': inputs.file_name
                }
            )
            chunker_output = self.chunker.process(
                ChunkerInput(
                    contents=parser_output.contents,
                    file_name=inputs.file_name,
                )
            )
            logger.info(
                'Chunker Service completed',
                extra={
                    'file_name': inputs.file_name
                }
            )
        except Exception as e:
            logger.exception(
                'Chunker Service failed',
                extra={
                    'file_name': inputs.file_name,
                    'error': str(e)
                }
            )
            
        try:
            logger.info(
                'Starting Builder Service',
                extra={
                    'file_name': inputs.file_name
                }
            )
            builder_output = await self.builder.process(
                BuilderInput(
                    chunks=[
                        {
                            "chunk_id": str(uuid4()),
                            "chunk_text": text
                        }
                        for text in chunker_output.chunks
                    ],
                    document_file_name=inputs.file_name
                )
            )
            logger.info(
                'Builder Service completed',
                extra={
                    'file_name': inputs.file_name
                }
            )
        except Exception as e:
            logger.exception(
                'Builder Service failed',
                extra={
                    'file_name': inputs.file_name,
                    'error': str(e)
                }
            )
            
        return IndexingApplicationOutput()


