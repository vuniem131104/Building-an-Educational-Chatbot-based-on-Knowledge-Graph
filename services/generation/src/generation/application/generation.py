from __future__ import annotations

import asyncio

from base import BaseModel 
from base import BaseApplication
from logger import get_logger
from fastapi import Request

from generation.domain.quiz_generation import QuizGenerationInput 
from generation.domain.quiz_generation import QuizGenerationService
from generation.domain.exam_generation import ExamGenerationInput
from generation.domain.exam_generation import ExamGenerationService
from generation.domain.parser import ParserInput
from generation.domain.parser import ParserService
from generation.domain.lecture_summarizer import LectureSummarizerInput
from generation.domain.lecture_summarizer import LectureSummarizerService
from generation.shared.models import AssessmentType
from generation.shared.models import Questions
from generation.shared.models import GenerationType
from generation.shared.settings import Settings


logger = get_logger(__name__)


class GenerationApplicationInput(BaseModel):
    assessment_type: AssessmentType
    generation_type: GenerationType
    num_questions: int
    num_multiple_choice: int | None = None
    num_essay: int | None = None
    course_code: str
    week_number: int | None = None 
    start_week: int | None = None
    end_week: int | None = None
    
    
class GenerationApplicationOutput(BaseModel):
    questions: Questions
    course_code: str
    week_number: int | None = None
    start_week: int | None = None
    end_week: int | None = None
    

class GenerationApplication(BaseApplication):
    
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
    def lecture_summarizer_service(self) -> LectureSummarizerService:
        """Get the Lecture Summarizer service."""
        return LectureSummarizerService(
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service,
            settings=self.settings.lecture_summarizer,
        )
    
    @property
    def quiz_generation_service(self) -> QuizGenerationService:
        """Get the Quiz Generation service."""
        return QuizGenerationService(
            quiz_settings=self.settings.quiz,
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service,
        )
        
    @property
    def exam_generation_service(self) -> ExamGenerationService:
        """Get the Exam Generation service."""
        return ExamGenerationService(
            exam_settings=self.settings.exam,
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service,
        )

    async def run(self, inputs: GenerationApplicationInput) -> GenerationApplicationOutput:
        if inputs.assessment_type == AssessmentType.QUIZ:
            if not inputs.week_number:
                raise ValueError("Week number is required for quiz generation")

            return await self.generate_quiz(inputs)
        elif inputs.assessment_type == AssessmentType.EXAM:
            if not inputs.start_week or not inputs.end_week:
                raise ValueError("Start and end weeks are required for exam generation")
            
            return await self.generate_exam(inputs)
        else:
            raise ValueError("Invalid assessment type")
        
    async def generate_exam(self, inputs: GenerationApplicationInput):
        
        try:
            semaphore = asyncio.Semaphore(self.settings.exam.max_concurrent_tasks)
            
            async def process_with_semaphore(inputs: GenerationApplicationInput):
                async with semaphore:
                    return await self.generate_quiz(
                        inputs=inputs
                    )
                    
            tasks = [
                process_with_semaphore(
                    inputs=GenerationApplicationInput(
                        assessment_type=AssessmentType.QUIZ,
                        generation_type=inputs.generation_type,
                        num_questions=inputs.num_questions,
                        course_code=inputs.course_code,
                        week_number=week_number,
                    )
                )
                for week_number in range(inputs.start_week, inputs.end_week + 1)
            ]
            
            results = await asyncio.gather(*tasks)
            
            results = sorted(results, key=lambda x: x.week_number)
            
            inputs = [(result.week_number, result.questions) for result in results]
            
            exam = await self.exam_generation_service.process(
                inputs=ExamGenerationInput(
                    start_week=inputs.start_week,
                    end_week=inputs.end_week,
                    questions=inputs,
                )
            )
            
            return GenerationApplicationOutput(
                questions=exam.questions,
                start_week=exam.start_week,
                end_week=exam.end_week,
                course_code=exam.course_code,
            )

        except Exception as e:
            logger.exception(
                "Error occurred while generating exam",
                extra={
                    'course_code': inputs.course_code,
                    'start_week': inputs.start_week,
                    'end_week': inputs.end_week,
                    'error': str(e)
                }
            )

    async def generate_quiz(self, inputs: GenerationApplicationInput) -> GenerationApplicationOutput:
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
                "Starting lecture summarizer service",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            
            _ = await self.lecture_summarizer_service.process(
                LectureSummarizerInput(
                    contents=parser_output.contents,
                    course_code=inputs.course_code,
                    week_number=inputs.week_number
                )
            )
            
            logger.info(
                "Lecture summarizer service completed successfully",
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
        except Exception as e:
            logger.exception(
                "Error occurred while summarizing lecture",
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
            
            return GenerationApplicationOutput(
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
