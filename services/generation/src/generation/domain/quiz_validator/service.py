from __future__ import annotations

from typing import Any
import json 

from generation.shared.settings.quiz_validator import QuizValidatorSetting
from generation.domain.quiz_validator.prompts import QUIZ_VALIDATOR_SYSTEM_PROMPT
from generation.shared.utils import filter_files

from lite_llm import LiteLLMInput
from lite_llm import LiteLLMService
from lite_llm import CompletionMessage 
from lite_llm import Role
from base import BaseModel
from base import BaseService
from logger import get_logger
from storage.minio import MinioService
from storage.minio import MinioInput


logger = get_logger(__name__)

class QuizValidatorInput(BaseModel):
    week_number: int
    course_code: str
    
class QuizValidatorOutput(BaseModel):
    score: int 
    explanation: str
    # answer: str


class QuizValidatorService(BaseService):
    settings: QuizValidatorSetting 
    litellm_service: LiteLLMService
    minio_service: MinioService
    
    async def process(
        self, inputs: QuizValidatorInput
    ) -> QuizValidatorOutput:
        """Validate quiz questions against lecture content.

        Args:
            inputs (QuizValidatorInput): The input data containing lecture content and quiz questions.

        Returns:
            QuizValidatorOutput: The output containing the validation score.
        """
        
        try:
            contents: list[str] = []
            files = self.minio_service.list_files(
                bucket_name=inputs.course_code, 
                prefix=f"tuan-{inputs.week_number}/",
                recursive=False
            )
            
            filtered_files = filter_files(files)
            
            for file in filtered_files:
                file_path = f"{inputs.course_code}/{file}"
                filename = file_path.split('/')[-1]
                
                contents.append(
                    self.minio_service.get_data_from_file(
                        MinioInput(
                            bucket_name=inputs.course_code,
                            object_name=f"tuan-{inputs.week_number}/{filename.split('.')[0]}_parser.txt"
                        )
                    )
                )
                
            quiz_questions = self.minio_service.get_data_from_file(
                MinioInput(
                    bucket_name=inputs.course_code,
                    object_name=f"tuan-{inputs.week_number}/quiz_questions.json"
                )
            )
            
            quiz_questions = json.loads(quiz_questions)['questions']
            
            prefix_user_prompt = """
            Return the answer in the following json format to dump the response into a json file:
            {
                "score": "<your score for the quiz>",
                "explanation": "<your_explanation why yout give that score>"
            }
            """
            output = await self.litellm_service.process_async(
                LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.USER,
                            content=QUIZ_VALIDATOR_SYSTEM_PROMPT,
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=self.build_quiz_context(
                                lecture_content="\n".join(contents),
                                quiz_questions=quiz_questions
                            )
                        )
                    ],
                    response_format=QuizValidatorOutput,
                    model=self.settings.model,
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                )
            )
        
            return output.response
        except Exception as e:
            logger.exception(
                "Error processing quiz validation",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "error": str(e)
                }
            )
            raise e
    
    
    def build_quiz_context(self, lecture_content: str, quiz_questions: list[dict[str, Any]]) -> str:
        """Build the context for the quiz validation.

        Args:
            lecture_content (str): The content of the lecture.
            quiz_questions (list[dict[str, Any]]): The list of quiz questions.

        Returns:
            str: The formatted context string.
        """
        quiz_contents: str = f"Lecture Content:\n{lecture_content}\n\nQuiz Questions:\n"
        for i, item in enumerate(quiz_questions):
            quiz_contents += f"Question {i + 1}: {item['question']}\n"
            if item.get('options', None):
                quiz_contents += "Options:\n"
                for option in item['options']:
                    quiz_contents += f"- {option}\n"
            if item.get('answer', None):
                quiz_contents += f"Answer: {item['answer']}\n"
            if item.get('explanation', None):
                quiz_contents += f"Explanation: {item['explanation']}\n"
            if item.get('level', None):
                quiz_contents += f"Difficulty: {item['level']}\n"
        return quiz_contents
    

# if __name__ == "__main__":
#     import json 
#     import asyncio 
#     import io 
#     from lite_llm import LiteLLMSetting
#     from pydantic import HttpUrl
#     from storage.minio import MinioSetting


#     model = "gemini-2.0-flash"

#     litellm_service=LiteLLMService(
#             litellm_setting=LiteLLMSetting(
#                 url=HttpUrl("http://localhost:9510"),
#                 token="abc123",
#                 model=model,
#                 frequency_penalty=0.0,
#                 n=1,
#                 temperature=0.0,
#                 top_p=1.0,
#                 max_completion_tokens=10000,
#             )
#         )
    
#     settings = QuizValidatorSetting(
#         model=model,
#         temperature=0.0,
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=8192,
#     )
    
#     service = QuizValidatorService(
#         litellm_service=litellm_service,
#         settings=settings,
#         minio_service=MinioService(
#             settings=MinioSetting(
#                 endpoint="localhost:9000",
#                 access_key="minioadmin",
#                 secret_key="minioadmin123",
#                 secure=False    
#             )
#         )
#     )

#     week_number = 3

#     inputs = QuizValidatorInput(
#         week_number=week_number,
#         course_code="int3405"
#     )
#     outputs = asyncio.run(service.process(inputs))
    
#     print(outputs)

#     with open(f'/home/vuiem/KLTN/test/validation/{model}/tuan-{week_number}.json', 'w', encoding='utf-8') as f:
#         json.dump(outputs.model_dump(), f, ensure_ascii=False, indent=4)