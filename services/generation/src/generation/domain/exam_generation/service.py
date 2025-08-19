from __future__ import annotations

import os 
import asyncio
import json 
import shutil
from base import BaseService
from logger import get_logger
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from generation.domain.exam_generation.prompts import EXAM_GENERATION_SYSTEM_PROMPT

from generation.shared.models import Questions
from generation.shared.models import GenerationBaseInput
from generation.shared.models import GenerationBaseOutput
from generation.shared.models import GenerationType
from generation.shared.models import Questions
from generation.shared.utils import filter_files
from generation.shared.settings import ExamGenerationSetting
from storage.minio import MinioInput
from storage.minio import MinioService


logger = get_logger(__name__)

class ExamGenerationInput(GenerationBaseInput):
    start_week: int 
    end_week: int
    questions: list[tuple[int, Questions]]
    

class ExamGenerationOutput(GenerationBaseOutput):
    start_week: int
    end_week: int
    questions: Questions


class ExamGenerationService(BaseService):

    exam_settings: ExamGenerationSetting
    litellm_service: LiteLLMService
    minio_service: MinioService
    
    async def process(self, inputs: ExamGenerationInput) -> ExamGenerationOutput:
        """Generate exam questions based on the input type and number of questions.

        Args:
            inputs (ExamGenerationInput): The input containing generation type and number of questions.

        Returns:
            ExamGenerationOutput: The generated exam questions.
        """
        try:
            context = self._build_context(inputs)
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=EXAM_GENERATION_SYSTEM_PROMPT,
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=context 
                        )
                    ],
                    response_format=Questions,
                    model=self.exam_settings.model,
                    temperature=self.exam_settings.temperature,
                    top_p=self.exam_settings.top_p,
                    n=self.exam_settings.n,
                    frequency_penalty=self.exam_settings.frequency_penalty,
                    max_completion_tokens=self.exam_settings.max_completion_tokens,
                    reasoning_effort=self.exam_settings.reasoning_effort,
                )
            )
            return ExamGenerationOutput(
                questions=output.response,
                start_week=inputs.start_week,
                end_week=inputs.end_week,
                course_code=inputs.course_code,
            )

        except Exception as e:
            logger.exception(
                'Error processing exam generation',
                extra={
                    'course_code': inputs.course_code,
                    'start_week': inputs.start_week,
                    'end_week': inputs.end_week,
                    'error': str(e),
                }
            )
            return ExamGenerationOutput(
                questions=[],
                start_week=inputs.start_week,
                end_week=inputs.end_week,
                course_code=inputs.course_code,
            )

    
    def _build_context(self, inputs: ExamGenerationInput) -> str:
        """Build context from sorted outputs.

        Args:
            inputs (ExamGenerationInput): The input containing exam generation details.

        Returns:
            str: The built context string.
        """
        context: str = ""
        for week_number, questions in inputs.questions:
            context += f"## Week {week_number}:\n"
            for i, question in enumerate(questions.questions):
                context += f"- Question {i + 1}: {question.question}\n"
                if question.options:
                    context += "  - Options:\n"
                    for option in question.options:
                        context += f"    - {option}\n"
                context += f"  - Answer: {question.answer}\n"
                if question.explanation:
                    context += f"  - Explanation: {question.explanation}\n"
                context += f"  - Difficulty: {question.level}\n"
            context += "\n"
        return context
    