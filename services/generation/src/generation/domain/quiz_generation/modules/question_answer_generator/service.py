from __future__ import annotations

from chromadb.api import ClientAPI
from pydantic import Field
from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import LiteLLMEmbeddingInput
from lite_llm import CompletionMessage
from lite_llm import Role
from generation.domain.quiz_generation.prompts import QUESTION_ANSWER_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import QUESTION_ANSWER_USER_PROMPT
from generation.domain.quiz_generation.modules.topics_generator import Topic
from generation.shared.settings import QuestionAnswerGeneratorSetting
from logger import get_logger

logger = get_logger(__name__)

class QuestionAnswer(BaseModel):
    question: str = Field(..., description="The generated question")
    answer: str = Field(..., description="The generated answer")

class QuestionAnswerGeneratorInput(BaseModel):
    topic: Topic
    week_number: int
    course_code: str 

class QuestionAnswerGeneratorOutput(BaseModel):
    question_answer: QuestionAnswer
    week_number: int
    course_code: str
    

class QuestionAnswerGeneratorService(BaseService):
    litellm_service: LiteLLMService
    settings: QuestionAnswerGeneratorSetting
    chromadb_client: ClientAPI

    async def process(self, inputs: QuestionAnswerGeneratorInput) -> QuestionAnswerGeneratorOutput:
        try:
            collection = self.chromadb_client.get_or_create_collection(name=self.settings.collection_name)
            query = inputs.topic.name
            embeddings = await self.litellm_service.embedding_llm_async(
                inputs=LiteLLMEmbeddingInput(
                    text=query
                )
            )
            results = collection.query(
                query_embeddings=[embeddings.embedding],
                n_results=3
            )
            
            examples: list[tuple[str, str]] = []
            
            for document, metadata in zip(results['documents'][0], results['metadatas'][0]):
                examples.append((document, metadata['answer']))
                
            if examples:
                formatted_examples = "Here are some examples of high-quality question-answer pairs to guide your generation:\n\n" + "\n\n".join(
                    [f"Example {i+1}:\nQuestion: {q}\nAnswer: {a}" for i, (q, a) in enumerate(examples)]
                ) + "\n\nUse these examples as reference for the style, clarity, and appropriateness of questions and answers. Generate a similar quality question-answer pair for the given topic."
            else:
                formatted_examples = "No similar examples available. Generate a high-quality question-answer pair based on the guidelines above."

            logger.info(
                "Retrieved similar questions from database",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "topic_name": inputs.topic.name,
                    "similar_questions_count": len(examples),
                    "formatted_examples": formatted_examples
                }
            )
        except Exception as e:
            logger.exception(
                "Error when retrieving similar questions from database",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": inputs.topic.name,
                    "error": str(e),
                } 
            )
            formatted_examples = "No similar examples available. Generate a high-quality question-answer pair based on the guidelines above."
            
        try:
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    model=self.settings.model,
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=QUESTION_ANSWER_SYSTEM_PROMPT.format(
                                examples=formatted_examples
                            )
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=QUESTION_ANSWER_USER_PROMPT.format(
                                topic_name=inputs.topic.name,
                                topic_description=inputs.topic.description,
                                difficulty_level=inputs.topic.difficulty_level,
                                bloom_taxonomy_level=inputs.topic.bloom_taxonomy_level,
                                estimated_right_answer_rate=inputs.topic.estimated_right_answer_rate
                            )
                        )
                    ],
                    response_format=QuestionAnswer,
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                    reasoning_effort=self.settings.reasoning_effort,
                )
            )
            
            logger.info(
                "Question-Answer generated successfully",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "topic_name": inputs.topic.name,
                }
            )

            return QuestionAnswerGeneratorOutput(
                question_answer=output.response,
                week_number=inputs.week_number,
                course_code=inputs.course_code
            )

        except Exception as e:
            logger.exception(
                "Error when processing question-answer generation with litellm",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": inputs.topic.name,
                    "error": str(e),
                } 
            )
            raise e


# if __name__ == "__main__":
#     from lite_llm import LiteLLMSetting
#     from chromadb import PersistentClient
#     from generation.shared.settings import QuestionAnswerGeneratorSetting
#     import asyncio
#     from pydantic import HttpUrl, SecretStr
#     client = PersistentClient(path="/home/vuiem/KLTN/chroma_database")

#     # Mock topic for testing
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
    
#     settings = QuestionAnswerGeneratorSetting(
#         model="gemini-2.5-flash",
#         temperature=0.0,
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         collection_name="questions",
#         reasoning_effort="medium"
#     )

#     litellm_service = LiteLLMService(litellm_setting=litellm_setting)
#     qa_generator_service = QuestionAnswerGeneratorService(
#         litellm_service=litellm_service,
#         settings=settings,
#         chromadb_client=client
#     )

#     async def test():
#         output = await qa_generator_service.process(
#             inputs=QuestionAnswerGeneratorInput(
#                 topic=mock_topic,
#                 week_number=6,
#                 course_code="int3405"
#             )
#         )
#         print(output)

#     asyncio.run(test())
