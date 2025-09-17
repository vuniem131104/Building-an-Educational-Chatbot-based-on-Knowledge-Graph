from generation.domain.quiz_generation.modules.question_answer_generator.service import QuestionAnswer
from generation.domain.quiz_generation.prompts import DISTRACTORS_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import DISTRACTORS_USER_PROMPT
from generation.shared.settings import DistractorsGeneratorSetting
from generation.shared.models import Topic

from pydantic import Field

from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from logger import get_logger


logger = get_logger(__name__)

class Distractors(BaseModel):
    distractors: list[str] = Field(..., description="List of generated distractors for the question")


class DistractorsGeneratorInput(BaseModel):
    question_answer: QuestionAnswer
    common_mistakes: list[str]
    topic: Topic
    week_number: int
    course_code: str
    
    
class DistractorsGeneratorOutput(BaseModel):
    distractors: list[str]
    week_number: int
    course_code: str
    
class DistractorsGeneratorService(BaseService):
    settings: DistractorsGeneratorSetting
    litellm_service: LiteLLMService

    async def process(self, inputs: DistractorsGeneratorInput) -> DistractorsGeneratorOutput:
        try:
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=DISTRACTORS_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=DISTRACTORS_USER_PROMPT.format(
                                question=inputs.question_answer.question,
                                answer=inputs.question_answer.answer,
                                topic_name=inputs.topic.name,
                                topic_description=inputs.topic.description,
                                difficulty_level=inputs.topic.difficulty_level,
                                bloom_taxonomy_level=inputs.topic.bloom_taxonomy_level,
                                estimated_right_answer_rate=inputs.topic.estimated_right_answer_rate,
                                week_number=inputs.week_number,
                                course_code=inputs.course_code,
                                common_mistakes=', '.join(inputs.common_mistakes)
                            )
                        )
                    ],
                    response_format=Distractors,
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                    reasoning_effort=self.settings.reasoning_effort,
                )
            )
            
            
            return DistractorsGeneratorOutput(
                distractors=output.response.distractors[:3],
                week_number=inputs.week_number,
                course_code=inputs.course_code
            )
        except Exception as e:
            logger.exception(
                "Error when processing distractor generation with litellm",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": inputs.topic.name,
                    "question": inputs.question_answer.question,
                    "answer": inputs.question_answer.answer,
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

#     settings = DistractorsGeneratorSetting(
#         model="gemini-2.5-flash",
#         temperature=0.7,
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         reasoning_effort="medium"
#     )

#     litellm_service = LiteLLMService(litellm_setting=litellm_setting)
#     distractors_generator_service = DistractorsGeneratorService(
#         litellm_service=litellm_service,
#         settings=settings
#     )

#     async def test():
#         output = await distractors_generator_service.process(
#             inputs=DistractorsGeneratorInput(
#                 topic=mock_topic,
#                 common_mistakes=[
#                     "Misunderstanding that the kernel trick explicitly maps data to higher dimensions, leading to computational inefficiency.",
#                     "Confusing the curse of dimensionality with overfitting, not recognizing that high-dimensional spaces can lead to sparse data distributions.",
#                     "Assuming that all kernels will improve model performance without considering the specific problem context or data characteristics."
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

#     asyncio.run(test())
