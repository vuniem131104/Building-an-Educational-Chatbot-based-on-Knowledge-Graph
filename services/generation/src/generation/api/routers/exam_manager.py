from __future__ import annotations
 
from fastapi import APIRouter
from fastapi import Request
from logger import get_logger

from generation.api.helpers.exception_handler import ExceptionHandler
from generation.application.exam_generation import ExamGenerationApplication
from generation.application.exam_generation import ExamGenerationApplicationInput


logger = get_logger(__name__)

exam_router = APIRouter(
    prefix="/v1/exam"
)

@exam_router.post("/generate", tags=["exam"])
async def generate_exam_questions(
    request: Request,
    inputs: ExamGenerationApplicationInput,
):
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=__name__,
    )
    try:
        generation_app = ExamGenerationApplication(
            request=request,
            settings=request.app.state.settings
        )
        output = await generation_app.run(inputs)
        
        return exception_handler.handle_success(
            output.model_dump()
        )

    except Exception as e:
        return exception_handler.handle_exception(
            str(e),
            extra={
                "generation_type": inputs.generation_type,
                "num_questions": inputs.num_questions,
                "course_code": inputs.course_code,
                "start_week": inputs.start_week,
                "end_week": inputs.end_week,
            }
        )