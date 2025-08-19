from __future__ import annotations

import os 
import shutil
import io 
import json
from fastapi import UploadFile
from base import BaseService
from logger import get_logger
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from generation.domain.quiz_generation.prompts import QUIZ_GENERATION_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import USER_PROMPT
from generation.domain.quiz_generation.prompts import PREVIOUS_LESSONS_TEMPLATE
from generation.domain.quiz_generation.prompts import LEARNING_OUTCOMES_TEMPLATE
from generation.domain.quiz_generation.prompts import NUM_QUESTIONS_SECTION_TEMPLATE

from generation.shared.models import GenerationType
from generation.shared.models import GenerationBaseInput
from generation.shared.models import GenerationBaseOutput
from generation.shared.models import Questions
from generation.shared.utils import filter_files
from generation.shared.utils import get_lecture_learning_outcomes
from generation.shared.utils import get_previous_lectures
from generation.shared.utils import get_week_learning_outcomes
from generation.shared.settings import QuizGenerationSetting
from storage.minio import MinioInput
from storage.minio import MinioService


logger = get_logger(__name__)


class QuizGenerationInput(GenerationBaseInput):
    week_number: int 
    contents: str

class QuizGenerationOutput(GenerationBaseOutput):
    week_number: int  
    

class QuizGenerationService(BaseService):
    
    quiz_settings: QuizGenerationSetting
    litellm_service: LiteLLMService
    minio_service: MinioService

    async def process(self, inputs: QuizGenerationInput) -> QuizGenerationOutput:
        """Generate quiz questions based on the input type and number of questions.

        Args:
            inputs (QuizGenerationInput): The input containing generation type and number of questions.

        Returns:
            QuizGenerationOutput: The generated quiz questions.
        """
        try:
            if self.minio_service.check_object_exists(
                MinioInput(
                    bucket_name=inputs.course_code, 
                    object_name=f"tuan-{inputs.week_number}/{inputs.generation_type.value}_questions.json"
                )
            ): 
                logger.info(
                    'Quiz questions already exist for this week',
                    extra={
                        'course_code': inputs.course_code,
                        'week_number': inputs.week_number,
                    },
                )
                
                questions = json.loads(
                    self.minio_service.get_data_from_file(
                        MinioInput(
                            bucket_name=inputs.course_code,
                            object_name=f"tuan-{inputs.week_number}/{inputs.generation_type.value}_questions.json"
                        )
                    )
                )
                    
                return QuizGenerationOutput(
                    questions=Questions(**questions),
                    course_code=inputs.course_code,
                    week_number=inputs.week_number
                )
                
            previous_lectures = get_previous_lectures(
                minio_service=self.minio_service,
                course_code=inputs.course_code, 
                week_number=inputs.week_number
            )   
            
            course_learning_outcomes = get_lecture_learning_outcomes(
                minio_service=self.minio_service,
                course_code=inputs.course_code,
            )
            
            introduction, week_learning_outcomes = get_week_learning_outcomes(
                week_number=inputs.week_number,
                learning_outcomes=course_learning_outcomes,
            )
            
            logger.info(
                'Week learning outcomes retrieved',
                extra={
                    'introduction': introduction,
                    'week_learning_outcomes': week_learning_outcomes,
                }
            )
            
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=QUIZ_GENERATION_SYSTEM_PROMPT.format(
                                num_questions=inputs.num_multiple_choice + inputs.num_essay if inputs.generation_type == GenerationType.MIXED else inputs.num_questions,
                            )
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=USER_PROMPT.format(
                                content=inputs.contents,
                                learning_outcomes_section=LEARNING_OUTCOMES_TEMPLATE.format(
                                    introduction=introduction,
                                    learning_outcomes=week_learning_outcomes,
                                ),
                                previous_lessons_section="" if not previous_lectures else
                                PREVIOUS_LESSONS_TEMPLATE.format(
                                    previous_content="\n".join(previous_lectures)
                                ),
                                generation_type=inputs.generation_type.value,
                                num_questions=inputs.num_multiple_choice + inputs.num_essay if inputs.generation_type == GenerationType.MIXED else inputs.num_questions,
                                num_questions_section=NUM_QUESTIONS_SECTION_TEMPLATE.format(
                                    num_multiple_choice=inputs.num_multiple_choice,
                                    num_essay=inputs.num_essay,
                                ) if inputs.generation_type == GenerationType.MIXED else ""
                            )
                        )
                    ],
                    response_format=Questions,
                    model=self.quiz_settings.model,
                    temperature=self.quiz_settings.temperature,
                    top_p=self.quiz_settings.top_p,
                    n=self.quiz_settings.n,
                    frequency_penalty=self.quiz_settings.frequency_penalty,
                    max_completion_tokens=self.quiz_settings.max_completion_tokens,
                    reasoning_effort=self.quiz_settings.reasoning_effort,
                )
            )
            
            _ = self.minio_service.upload_data(
                MinioInput(
                    bucket_name=inputs.course_code,
                    object_name=f"tuan-{inputs.week_number}/{inputs.generation_type.value}_questions.json",
                    data=io.BytesIO(json.dumps(output.response.model_dump(), ensure_ascii=False).encode('utf-8'))
                )
            )
            
            return QuizGenerationOutput(
                questions=output.response,
                course_code=inputs.course_code,
                week_number=inputs.week_number,
            )
        except Exception as e:
            logger.exception(
                'Error processing quiz generation',
                extra={
                    'course_code': inputs.course_code,
                    'week_number': inputs.week_number,
                    'error': str(e),
                },
            )
            return QuizGenerationOutput(
                questions=[],
                course_code=inputs.course_code,
                week_number=inputs.week_number,
            )
        finally:
            shutil.rmtree(inputs.course_code)
            
