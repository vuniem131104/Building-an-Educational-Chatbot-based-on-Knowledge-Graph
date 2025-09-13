# from __future__ import annotations
 
# from fastapi import APIRouter
# from fastapi import Request
# from logger import get_logger

# from generation.api.helpers.exception_handler import ExceptionHandler
# from generation.application.quiz_generation import QuizGenerationApplication
# from generation.application.quiz_generation import QuizGenerationApplicationInput


# logger = get_logger(__name__)

# quiz_router = APIRouter(
#     prefix="/v1/quiz"
# )

# @quiz_router.post("/generate", tags=["quiz"])
# async def generate_quiz_questions(
#     request: Request,
#     inputs: QuizGenerationApplicationInput,
# ):
#     exception_handler = ExceptionHandler(
#         logger=logger.bind(),
#         service_name=__name__,
#     )
#     try:
#         generation_app = QuizGenerationApplication(
#             request=request,
#             settings=request.app.state.settings
#         )
#         output = await generation_app.run(inputs)
        
#         return exception_handler.handle_success(
#             output.model_dump()
#         )

#     except Exception as e:
#         return exception_handler.handle_exception(
#             str(e),
#             extra={
#                 "generation_type": inputs.generation_type,
#                 "num_questions": inputs.num_questions,
#                 "course_code": inputs.course_code,
#                 "week_number": inputs.week_number,
#             }
#         )