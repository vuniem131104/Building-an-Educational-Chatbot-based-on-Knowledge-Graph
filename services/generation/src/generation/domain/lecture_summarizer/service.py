from __future__ import annotations 

import io
from base import BaseModel 
from base import BaseService
from logger import get_logger
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from storage.minio import MinioInput
from storage.minio import MinioService
from generation.domain.lecture_summarizer.prompts import LECTURE_SUMMARIZER_PROMPT
from generation.domain.lecture_summarizer.prompts import USER_PROMPT
from generation.shared.settings.lecture_summarizer import LectureSummarizerSetting


logger = get_logger(__name__)


class LectureSummarizerInput(BaseModel):
    contents: str
    course_code: str
    week_number: int

class LectureSummarizerOutput(BaseModel):
    summary: str
    course_code: str
    week_number: int


class LectureSummarizerService(BaseService):

    litellm_service: LiteLLMService
    settings: LectureSummarizerSetting
    minio_service: MinioService

    async def process(self, inputs: LectureSummarizerInput) -> LectureSummarizerOutput:
        """Summarizes the content of a lecture.

        Args:
            inputs (LectureSummarizerInput): The input data containing the lecture content.

        Returns:
            LectureSummarizerOutput: The output data containing the summary of the lecture.
        """
        try:
            if not inputs.contents:
                logger.warning(
                    'Lecture summarization skipped due to empty content',
                    extra={
                        'course_code': inputs.course_code,
                        'week_number': inputs.week_number
                    }
                )
                return LectureSummarizerOutput(
                    summary="",
                    course_code=inputs.course_code,
                    week_number=inputs.week_number
                )

            
            is_summary_exist = self.minio_service.check_object_exists(
                input=MinioInput(
                    bucket_name=inputs.course_code,
                    object_name=f"tuan-{inputs.week_number}/summary.txt"
                )
            )
            
            if is_summary_exist:
                logger.info(
                    "Summary file already exists, skipping processing",
                    extra={
                        "course_code": inputs.course_code,
                        "week_number": inputs.week_number
                    }
                )
                return LectureSummarizerOutput(
                    summary=self.minio_service.get_data_from_file(
                        MinioInput(
                            bucket_name=inputs.course_code,
                            object_name=f"tuan-{inputs.week_number}/summary.txt"
                        )
                    ),
                    course_code=inputs.course_code,
                    week_number=inputs.week_number
                )
            else:
                logger.info(
                    "Processing file for summarization",
                    extra={
                        "course_code": inputs.course_code,
                        "week_number": inputs.week_number
                    }
                )
        
                output = await self.litellm_service.process_async(
                    inputs=LiteLLMInput(
                        messages=[
                            CompletionMessage(
                                role=Role.SYSTEM,
                                content=LECTURE_SUMMARIZER_PROMPT
                            ),
                            CompletionMessage(
                                role=Role.USER,
                                content=USER_PROMPT.format(content=inputs.contents)
                            )
                        ],
                        model=self.settings.model,
                        temperature=self.settings.temperature,
                        top_p=self.settings.top_p,
                        n=self.settings.n,
                        frequency_penalty=self.settings.frequency_penalty,
                        max_completion_tokens=self.settings.max_completion_tokens,
                        resoning_effort=self.settings.reasoning_effort,
                    )
                )
                
                logger.info(
                    'Lecture summarization completed',
                    extra={
                        'summary': output.response,
                    }
                )

                _ = self.minio_service.upload_data(
                    MinioInput(
                        bucket_name=inputs.course_code,
                        object_name=f"tuan-{inputs.week_number}/summary.txt",
                        data=io.BytesIO(output.response.encode('utf-8'))
                    )
                )
                
            return LectureSummarizerOutput(
                summary=output.response,
                course_code=inputs.course_code,
                week_number=inputs.week_number
            )
        except Exception as e:
            logger.error(
                'Error during lecture summarization',
                extra={
                    'error': str(e),
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number
                }
            )
            
            return LectureSummarizerOutput(
                summary="",
                course_code=inputs.course_code,
                week_number=inputs.week_number
            )