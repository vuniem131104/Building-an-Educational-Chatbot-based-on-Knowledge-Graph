from generation.domain.quiz_generation.prompts import QUIZ_CORRECTION_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import QUIZ_CORRECTION_USER_PROMPT
from generation.shared.models import QuizQuestion
from generation.shared.settings import QuizCorrectionSetting

from pydantic import Field

from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from logger import get_logger


logger = get_logger(__name__)

class QuizQuestionResponse(BaseModel):
    question: str = Field(..., description="The quiz question text")
    answer: str = Field(..., description="The correct answer text")
    distractors: list[str] = Field(..., description="List of incorrect answer options")
    explanation: str = Field(..., description="Explanation for the correct answer and distractors")


class QuizCorrectionInput(BaseModel):
    validator_feedback: str
    question_metadata: QuizQuestion
    

class QuizCorrectionOutput(BaseModel):
    corrected_question: QuizQuestion
    

class QuizCorrectionService(BaseService):
    settings: QuizCorrectionSetting
    litellm_service: LiteLLMService

    async def process(self, inputs: QuizCorrectionInput) -> QuizCorrectionOutput:
        try:

            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=QUIZ_CORRECTION_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=QUIZ_CORRECTION_USER_PROMPT.format(
                                original_question=inputs.question_metadata.question,
                                original_answer=inputs.question_metadata.answer,
                                original_distractors_list="\n".join([f"- {distractor}" for distractor in inputs.question_metadata.distractors]),
                                original_explanation=inputs.question_metadata.explanation,
                                validator_feedback=inputs.validator_feedback,
                                topic_name=inputs.question_metadata.topic.name,
                                topic_description=inputs.question_metadata.topic.description,
                                difficulty_level=inputs.question_metadata.topic.difficulty_level,
                                bloom_taxonomy_level=inputs.question_metadata.topic.bloom_taxonomy_level,
                                course_code=inputs.question_metadata.course_code
                            )
                        )
                    ],
                    response_format=QuizQuestionResponse,
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                    reasoning_effort=self.settings.reasoning_effort,
                )
            )
            
            return QuizCorrectionOutput(
                corrected_question=QuizQuestion(
                    question=output.response.question,
                    answer=output.response.answer,
                    distractors=output.response.distractors,
                    explanation=output.response.explanation,
                    topic=inputs.question_metadata.topic,
                    course_code=inputs.question_metadata.course_code,
                    week_number=inputs.question_metadata.week_number
                )
            )
        except Exception as e:
            logger.exception(
                "Error when processing explanation generation with litellm",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": inputs.topic.name,
                    "question": inputs.question_answer.question,
                    "answer": inputs.question_answer.answer,
                    "distractors": inputs.distractors,
                    "error": str(e),
                } 
            )
            return QuizCorrectionOutput(
                corrected_question=inputs.question_metadata
            )

# if __name__ == "__main__":
#     from lite_llm import LiteLLMSetting
#     import asyncio
#     from pydantic import HttpUrl, SecretStr

#     mock_topic = Topic(
#         name="Perceptron Model Core Concepts",
#         description="This topic covers the fundamental definition of a perceptron, its role in linear classification, and the mathematical representation of decision boundaries in machine learning.",
#         difficulty_level="Easy",
#         estimated_right_answer_rate=0.85,
#         bloom_taxonomy_level="Remember"
#     )

#     litellm_setting = LiteLLMSetting(
#         url=HttpUrl("http://localhost:9510"),
#         token=SecretStr("abc123"),
#         model="claude-sonnet-4-20250514",
#         frequency_penalty=0.0,
#         n=1,
#         temperature=0.0,
#         top_p=1.0,
#         max_completion_tokens=10000,
#         dimension=1536,
#         embedding_model="gemini-embedding"
#     )

#     settings = ExplanationGeneratorSetting(
#         model="gpt-4o-mini",
#         temperature=0.2,
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         # reasoning_effort="medium"
#     )

#     litellm_service = LiteLLMService(litellm_setting=litellm_setting)
#     explanation_generator_service = ExplanationGeneratorService(
#         litellm_service=litellm_service,
#         settings=settings
#     )

#     async def test():
#         output = await explanation_generator_service.process(
#             inputs=ExplanationGeneratorInput(
#                 topic=mock_topic,
#                 distractors=[
#                     "Decision line", 
#                     "Activation function", 
#                     "Weight vector"
#                 ],
#                 question_answer=QuestionAnswer(
#                     question="In the context of a perceptron model, what is the term for the decision boundary that separates different classes of data?",
#                     answer="Separating hyperplane"
#                 ),
#                 week_number=6,
#                 course_code="int3405"
#             )
#         )
#         print(output)
#         import json
#         with open("explanation_output.json", "w", encoding='utf-8') as f:
#             json.dump(output.model_dump(), f, ensure_ascii=False, indent=4)
#     asyncio.run(test())