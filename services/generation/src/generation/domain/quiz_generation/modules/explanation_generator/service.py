from generation.domain.quiz_generation.modules.topics_generator import Topic
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


class DistractorExplanation(BaseModel):
    distractor: str = Field(..., description="The distractor text")
    explanation: str = Field(..., description="Explanation for the distractor")


class Explanation(BaseModel):
    correct_answer_explanation: str = Field(..., description="Explanation for the correct answer")
    distractors_explanation: list[DistractorExplanation]
    conceptual_summary: str = Field(..., description="Conceptual summary of the topic")
    learning_tips: str = Field(..., description="Learning tips related to the topic")


class ExplanationGeneratorInput(BaseModel):
    question_answer: QuestionAnswer
    distractors: list[str]
    topic: Topic
    week_number: int
    course_code: str
    

class ExplanationGeneratorOutput(BaseModel):
    explanation: Explanation
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
                    response_format=Explanation,
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
#         name="Kernel Trick and Dimensionality (Week 1 & 6)",
#         description="This cross-week topic (integrating Week 1 and Week 6) connects the 'Curse of Dimensionality' from Week 1 with the 'Kernel Trick' from Week 6. Students should analyze how the kernel trick implicitly maps data to higher-dimensional feature spaces to achieve linear separability, and how this process, while beneficial for non-linear problems, relates to the computational challenges and potential pitfalls associated with high-dimensional spaces if not managed implicitly. MCQs can explore the trade-offs or the conceptual connection between these two ideas.",
#         difficulty_level="Hard",
#         estimated_right_answer_rate=0.35,
#         bloom_taxonomy_level="Analyze"
#     )

#     litellm_setting = LiteLLMSetting(
#         url=HttpUrl("http://localhost:9510"),
#         token=SecretStr("abc123"),
#         model="gemini-2.5-flash",
#         frequency_penalty=0.0,
#         n=1,
#         temperature=0.0,
#         top_p=1.0,
#         max_completion_tokens=10000,
#         dimension=1536,
#         embedding_model="gemini-embedding"
#     )

#     settings = ExplanationGeneratorSetting(
#         model="gemini-2.5-flash",
#         temperature=0.0,
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         reasoning_effort="medium"
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
#                     "The kernel trick explicitly maps each data point to its corresponding high-dimensional feature vector, but it uses a highly optimized mathematical function to perform this mapping very quickly, making the process computationally feasible.", 
#                     "The kernel trick combats the curse of dimensionality by projecting the sparse high-dimensional data onto a lower-dimensional manifold where it becomes denser and less prone to overfitting, simplifying classification.", 
#                     "The kernel trick effectively eliminates the 'Curse of Dimensionality' by creating a new feature space where data points are always more spread out and linearly separable, ensuring that any classification algorithm will perform optimally without increased computational burden."
#                 ],
#                 question_answer=QuestionAnswer(
#                     question="The 'Curse of Dimensionality' describes the exponential increase in computational complexity and data sparsity as the number of features grows. Considering this, how does the 'Kernel Trick' enable classification in implicitly higher-dimensional spaces without explicitly incurring the severe computational costs typically associated with such high dimensions?",
#                     answer="The kernel trick computes the dot product of feature vectors in the original, lower-dimensional space, which is equivalent to the dot product in the higher-dimensional space, thus avoiding the explicit transformation and computation of coordinates in the high-dimensional feature space."
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