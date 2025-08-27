from __future__ import annotations

from base import BaseModel 
from base import BaseApplication
from logger import get_logger
from fastapi import Request

from generation.domain.exam_generation import ExamGenerationInput 
from generation.domain.exam_generation import ExamGenerationService
from generation.domain.exam_generation import ExamGenerationOutput
from generation.shared.models import GenerationType
from generation.shared.settings import Settings


logger = get_logger(__name__)


class ExamGenerationApplicationInput(ExamGenerationInput):
    pass

class ExamGenerationApplicationOutput(ExamGenerationOutput):
    pass

class ExamGenerationApplication(BaseApplication):

    request: Request 
    settings: Settings
    
    @property
    def exam_generation_service(self) -> ExamGenerationService:
        return ExamGenerationService(
            exam_settings=self.settings.exam,
            litellm_service=self.request.app.state.litellm_service,
            minio_service=self.request.app.state.minio_service,
        )

    async def run(self, inputs: ExamGenerationApplicationInput) -> ExamGenerationApplicationOutput:
        try:
            logger.info(
                "Starting Exam generation service",
                extra={
                    'course_code': inputs.course_code,
                    'start_week': inputs.start_week,
                    'end_week': inputs.end_week
                }
            )
            output = await self.exam_generation_service.process(inputs)
            logger.info(
                "Exam generation service completed successfully",
                extra={
                    'course_code': inputs.course_code,
                    'start_week': inputs.start_week,
                    'end_week': inputs.end_week
                }
            )
            return ExamGenerationApplicationOutput(
                course_code=inputs.course_code,
                start_week=inputs.start_week,
                end_week=inputs.end_week,
                questions=output.questions,
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
            