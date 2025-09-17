from generation.shared.models import Topic
from generation.domain.quiz_generation.prompts import EXPLANATION_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import EXPLANATION_USER_PROMPT
from generation.shared.settings import ExplanationGeneratorSetting
from generation.domain.quiz_generation.modules.question_answer_generator.service import QuestionAnswer

from pydantic import Field

from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from logger import get_logger


logger = get_logger(__name__)


class ExplanationGeneratorInput(BaseModel):
    question_answer: QuestionAnswer
    distractors: list[str]
    topic: Topic
    week_number: int
    course_code: str
    

class ExplanationGeneratorOutput(BaseModel):
    explanation: str
    week_number: int
    course_code: str
    

class ExplanationGeneratorService(BaseService):
    settings: ExplanationGeneratorSetting
    litellm_service: LiteLLMService

    async def process(self, inputs: ExplanationGeneratorInput) -> ExplanationGeneratorOutput:
        try:
            distractors_list = "\n".join([f"- {distractor}" for distractor in inputs.distractors])
            
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=EXPLANATION_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=EXPLANATION_USER_PROMPT.format(
                                question=inputs.question_answer.question,
                                answer=inputs.question_answer.answer,
                                distractors_list=distractors_list,
                                topic_name=inputs.topic.name,
                                topic_description=inputs.topic.description,
                                difficulty_level=inputs.topic.difficulty_level,
                                bloom_taxonomy_level=inputs.topic.bloom_taxonomy_level,
                                estimated_right_answer_rate=inputs.topic.estimated_right_answer_rate,
                                week_number=inputs.week_number,
                                course_code=inputs.course_code
                            )
                        )
                    ],
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                    reasoning_effort=self.settings.reasoning_effort,
                )
            )
            
            return ExplanationGeneratorOutput(
                explanation=output.response,
                week_number=inputs.week_number,
                course_code=inputs.course_code
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
            raise e

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