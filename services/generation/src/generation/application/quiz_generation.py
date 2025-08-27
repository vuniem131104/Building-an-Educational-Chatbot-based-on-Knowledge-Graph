from __future__ import annotations

from base import BaseModel 
from base import BaseApplication
from logger import get_logger
from fastapi import Request

from generation.domain.quiz_generation import QuizGenerationInput 
from generation.domain.quiz_generation import QuizGenerationService
from generation.domain.quiz_generation import QuizGenerationOutput
from generation.domain.parser import ParserInput
from generation.domain.parser import ParserService
from generation.shared.models import GenerationType
from generation.shared.settings import Settings


logger = get_logger(__name__)


class QuizGenerationApplicationInput(BaseModel):
    week_number: int 
    course_code: str
    generation_type: GenerationType = GenerationType.MULTIPLE_CHOICE
    num_questions: int
    num_multiple_choice: int = 0
    num_essay: int = 0    
    
class QuizGenerationApplicationOutput(QuizGenerationOutput):
    pass

class QuizGenerationApplication(BaseApplication):

    request: Request 
    settings: Settings
    
    @property 
    def parser_service(self) -> ParserService:
        """Get the Parser service."""
        return ParserService(
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service,
            settings=self.settings.parser,
        )
    
    @property
    def quiz_generation_service(self) -> QuizGenerationService:
        """Get the Quiz Generation service."""
        return QuizGenerationService(
            quiz_settings=self.settings.quiz,
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service,
        )
        
    async def run(self, inputs: QuizGenerationApplicationInput) -> QuizGenerationApplicationOutput:
        try:
            logger.info(
                "Starting parser service to process lecture files",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            parser_output = await self.parser_service.process(
                ParserInput(
                    course_code=inputs.course_code,
                    week_number=inputs.week_number
                )
            )
            logger.info(
                "Parser service completed successfully",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
        except Exception as e:
            logger.exception(
                "Error occurred while processing lecture files",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number,
                    'error': str(e)
                }
            )
            
        try:
            logger.info(
                "Starting quiz generation service",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            quiz_output = await self.quiz_generation_service.process(
                QuizGenerationInput(
                    generation_type=inputs.generation_type,
                    num_questions=inputs.num_questions,
                    num_multiple_choice=inputs.num_multiple_choice,
                    num_essay=inputs.num_essay,
                    course_code=inputs.course_code,
                    week_number=inputs.week_number,
                    contents=parser_output.contents
                )
            )
            logger.info(
                "Quiz generation service completed successfully",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            
            return QuizGenerationApplicationOutput(
                questions=quiz_output.questions,
                course_code=inputs.course_code,
                week_number=inputs.week_number,
            )
        except Exception as e:
            logger.exception(
                "Error occurred while generating quiz",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number,
                    'error': str(e)
                }
            )