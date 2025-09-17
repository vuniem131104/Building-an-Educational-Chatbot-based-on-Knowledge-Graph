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


from logger import get_logger


logger = get_logger(__name__)

class IndexingApplicationInput(BaseModel):
    course_code: str 
    week_number: int
    

class IndexingApplicationOutput(BaseModel):
    pass 

class IndexingApplication(BaseApplication):
    
    request: Request

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
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            parser_output = await self.parser.process(
                ParserInput(
                    course_code=inputs.course_code,
                    week_number=inputs.week_number
                )
            )
            logger.info(
                'Parser Service completed',
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
        except Exception as e:
            logger.exception(
                'Parser Service failed',
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number,
                    'error': str(e)
                }
            )
            
        try:
            logger.info(
                'Starting Chunker Service',
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            chunker_output = self.chunker.process(
                ChunkerInput(
                    contents=parser_output.contents,
                    file_name=parser_output.file_name,
                )
            )
            logger.info(
                'Chunker Service completed',
                extra={
                    "number_of_chunks": len(chunker_output.chunks),
                }
            )
        except Exception as e:
            logger.exception(
                'Chunker Service failed',
                extra={
                    'file_name': parser_output.file_name,
                    'error': str(e)
                }
            )
            
        try:
            logger.info(
                'Starting Builder Service',
                extra={
                    'file_name': parser_output.file_name
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
                    document_file_name=parser_output.file_name
                )
            )
            logger.info(
                'Builder Service completed',
                extra={
                    'file_name': parser_output.file_name,
                }
            )
        except Exception as e:
            logger.exception(
                'Builder Service failed',
                extra={
                    'file_name': parser_output.file_name,
                    'error': str(e)
                }
            )
            
        return IndexingApplicationOutput()


