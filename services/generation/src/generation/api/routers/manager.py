from __future__ import annotations
 
from fastapi import APIRouter
from fastapi import Request
from logger import get_logger

from generation.api.helpers.exception_handler import ExceptionHandler
from generation.application.generation import GenerationApplication
from generation.application.generation import GenerationApplicationInput


logger = get_logger(__name__)

main_router = APIRouter(
    prefix="/v1"
)

@main_router.post("/generate")
async def generate_question(
    request: Request,
    inputs: GenerationApplicationInput,
):
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=__name__,
    )
    try:
        generation_app = GenerationApplication(
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
                "assessment_type": inputs.assessment_type,
                "generation_type": inputs.generation_type,
                "num_questions": inputs.num_questions,
                "course_code": inputs.course_code,
                "week_number": inputs.week_number,
                "start_week": inputs.start_week,
                "end_week": inputs.end_week
            }
        )

@main_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}