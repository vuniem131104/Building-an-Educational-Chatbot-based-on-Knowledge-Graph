from __future__ import annotations

import asyncio
from chromadb.api import ClientAPI

from generation.domain.quiz_generation.modules.concept_card_extractor import ConceptCardExtractorService
from generation.domain.quiz_generation.modules.concept_card_extractor import ConceptCardExtractorInput
from generation.domain.quiz_generation.modules.concept_card_extractor import ConceptCard

from generation.domain.quiz_generation.modules.topics_generator import TopicGeneratorService
from generation.domain.quiz_generation.modules.topics_generator import TopicGeneratorInput
from generation.domain.quiz_generation.modules.topics_generator import Topic

from generation.domain.quiz_generation.modules.question_answer_generator import QuestionAnswerGeneratorService
from generation.domain.quiz_generation.modules.question_answer_generator import QuestionAnswerGeneratorInput

from generation.domain.quiz_generation.modules.distractors_generator import DistractorsGeneratorService
from generation.domain.quiz_generation.modules.distractors_generator import DistractorsGeneratorInput

from generation.domain.quiz_generation.modules.explanation_generator import ExplanationGeneratorService
from generation.domain.quiz_generation.modules.explanation_generator import ExplanationGeneratorInput
from generation.domain.quiz_generation.modules.explanation_generator import Explanation

from generation.shared.settings import QuizGenerationSetting

from base import BaseModel
from base import BaseService
from logger import get_logger
from storage.minio import MinioService

logger = get_logger(__name__)


class QuizQuestion(BaseModel):
    question: str
    answer: str
    distractors: list[str]
    explanation: Explanation
    topic: Topic
    week_number: int
    course_code: str


class QuizGenerationInput(BaseModel):
    number_of_topics: int
    common_mistakes: list[str]
    week_number: int
    course_code: str


class QuizGenerationOutput(BaseModel):
    topic: list[Topic]
    concept_cards: list[ConceptCard]
    quiz_questions: list[QuizQuestion]
    week_number: int
    course_code: str

class QuizGenerationService(BaseService):
    settings: QuizGenerationSetting
    litellm_service: LiteLLMService
    minio_service: MinioService
    chromadb_client: ClientAPI
    
    @property
    def concept_card_extractor_service(self) -> ConceptCardExtractorService:
        return ConceptCardExtractorService(
            litellm_service=self.litellm_service,
            settings=self.settings.concept_card_extractor,
            minio_service=self.minio_service
        )
    
    @property
    def topic_generator_service(self) -> TopicGeneratorService:
        return TopicGeneratorService(
            litellm_service=self.litellm_service,
            settings=self.settings.topic_generator
        )    

    @property
    def question_answer_generator_service(self) -> QuestionAnswerGeneratorService:
        return QuestionAnswerGeneratorService(
            litellm_service=self.litellm_service,
            settings=self.settings.question_answer_generator,
            chromadb_client=self.chromadb_client
        )

    @property
    def distractors_generator_service(self) -> DistractorsGeneratorService:
        return DistractorsGeneratorService(
            litellm_service=self.litellm_service,
            settings=self.settings.distractors_generator,
        )

    @property
    def explanation_generator_service(self) -> ExplanationGeneratorService:
        return ExplanationGeneratorService(
            litellm_service=self.litellm_service,
            settings=self.settings.explanation_generator,
        )

    async def process(self, inputs: QuizGenerationInput) -> QuizGenerationOutput:
        """
        Process quiz generation with try-catch for each module to ensure partial success.
        Even if some modules fail, we can still return partial results.
        """
        concept_cards = None
        topics = None
        # Step 1: Extract concept cards
        try:
            logger.info(
                "Starting concept card extraction",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                }
            )
            
            concept_card_output = await self.concept_card_extractor_service.process(
                ConceptCardExtractorInput(
                    week_number=inputs.week_number,
                    course_code=inputs.course_code
                )
            )
            concept_cards = concept_card_output.concept_cards
            
            logger.info(
                "Successfully extracted concept cards",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "concept_cards_count": len(concept_cards) if concept_cards else 0,
                }
            )
            
        except Exception as e:
            error_msg = "Concept card extraction failed"
            logger.exception(
                error_msg,
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "error": str(e),
                }
            )
            raise e

        # Step 2: Generate topics
        if concept_cards:
            try:
                logger.info(
                    "Starting topic generation",
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "number_of_topics": inputs.number_of_topics,
                    }
                )
                
                topic_output = await self.topic_generator_service.process(
                    TopicGeneratorInput(
                        previous_lectures=concept_card_output.previous_lectures,
                        lecture_learning_outcomes=concept_card_output.lecture_learning_outcomes,
                        concept_cards=concept_card_output.concept_cards,
                        number_of_topics=inputs.number_of_topics,
                        week_number=inputs.week_number,
                        course_code=inputs.course_code
                    )
                )
                topics = topic_output.topics.topics
                
                logger.info(
                    "Successfully generated topics",
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topics_count": len(topics),
                    }
                )
                
            except Exception as e:
                error_msg = f"Topic generation failed: {str(e)}"
                logger.exception(
                    error_msg,
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "error": str(e),
                    }
                )
                generation_errors.append(error_msg)
        else:
            error_msg = "Topic generation skipped: No concept cards available"
            logger.exception(error_msg, extra={
                "week_number": inputs.week_number,
                "course_code": inputs.course_code,
            })
            raise ValueError(error_msg)

        semaphore = asyncio.Semaphore(self.settings.max_concurrent_tasks)

        async def generate_with_semaphore(topic: Topic, inputs: QuizGenerationInput):
            async with semaphore:
                return await self._generate_quiz_for_topic(topic, inputs)

        # Step 3: Generate quiz questions for each topic
        if topics:
            quiz_questions = await asyncio.gather(
                *[generate_with_semaphore(topic, inputs) for topic in topics],
            )

            quiz_questions = [q for q in quiz_questions if q is not None]

        else:
            error_msg = "Quiz question generation skipped: No topics available"
            logger.warning(error_msg, extra={
                "week_number": inputs.week_number,
                "course_code": inputs.course_code,
            })

        logger.info(
            "Quiz generation completed",
            extra={
                "week_number": inputs.week_number,
                "course_code": inputs.course_code,
                "quiz_questions_count": len(quiz_questions),
            }
        )

        return QuizGenerationOutput(
            topic=topics if topics else [],
            concept_cards=concept_cards if concept_cards else [],
            quiz_questions=quiz_questions,
            week_number=inputs.week_number,
            course_code=inputs.course_code,
        )

    async def _generate_quiz_for_topic(self, topic: Topic, inputs: QuizGenerationInput) -> QuizQuestion | None:
        question_answer = None
        distractors = None
        explanation = None

        # Step 3a: Generate question and answer
        try:
            logger.info(
                f"Starting question-answer generation",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": topic.name,
                }
            )
            
            qa_output = await self.question_answer_generator_service.process(
                QuestionAnswerGeneratorInput(
                    topic=topic,
                    week_number=inputs.week_number,
                    course_code=inputs.course_code
                )
            )
            question_answer = qa_output.question_answer
            
            logger.info(
                f"Successfully generated question-answer",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": topic.name,
                    "question": question_answer.question,
                    "answer": question_answer.answer,
                }
            )
            
        except Exception as e:
            error_msg = f"Question-answer generation failed for topic '{topic.name}'"
            logger.exception(
                error_msg,
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": topic.name,
                    "error": str(e),
                }
            )
            return None

        # Step 3b: Generate distractors
        if question_answer:
            try:
                logger.info(
                    f"Starting distractors generation",
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topic_name": topic.name,
                    }
                )
                
                distractors_output = await self.distractors_generator_service.process(
                    DistractorsGeneratorInput(
                        question_answer=question_answer,
                        common_mistakes=inputs.common_mistakes,
                        topic=topic,
                        week_number=inputs.week_number,
                        course_code=inputs.course_code
                    )
                )
                distractors = distractors_output.distractors
                
                logger.info(
                    f"Successfully generated distractors",
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topic_name": topic.name,
                        "distractors_count": len(distractors),
                    }
                )
                
            except Exception as e:
                error_msg = f"Distractors generation failed for topic '{topic.name}': {str(e)}"
                logger.exception(
                    error_msg,
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topic_name": topic.name,
                        "error": str(e),
                    }
                )

        # Step 3c: Generate explanation
        if question_answer and distractors:
            try:
                logger.info(
                    f"Starting explanation generation",
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topic_name": topic.name,
                    }
                )
                
                explanation_output = await self.explanation_generator_service.process(
                    ExplanationGeneratorInput(
                        question_answer=question_answer,
                        distractors=distractors,
                        topic=topic,
                        week_number=inputs.week_number,
                        course_code=inputs.course_code
                    )
                )
                explanation = explanation_output.explanation
                
                logger.info(
                    f"Successfully generated explanation",
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topic_name": topic.name,
                    }
                )
                
            except Exception as e:
                error_msg = f"Explanation generation failed for topic '{topic.name}': {str(e)}"
                logger.exception(
                    error_msg,
                    extra={
                        "week_number": inputs.week_number,
                        "course_code": inputs.course_code,
                        "topic_name": topic.name,
                        "error": str(e),
                    }
                )

        # Add quiz question if we have at least question and answer
        if question_answer and distractors and explanation:
            
            logger.info(
                f"Successfully created quiz question",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "topic_name": topic.name,
                }
            )
            
            return QuizQuestion(
                question=question_answer.question,
                answer=question_answer.answer,
                distractors=distractors,
                explanation=explanation,
                topic=topic,
                week_number=inputs.week_number,
                course_code=inputs.course_code
            )
        
        return None


if __name__ == "__main__":
    import asyncio
    import json
    from lite_llm import LiteLLMService, LiteLLMSetting
    from pydantic import HttpUrl, SecretStr
    
    # Import settings
    from generation.shared.settings import (
        ConceptCardExtractorSetting,
        TopicGeneratorSetting,
        QuestionAnswerGeneratorSetting,
        DistractorsGeneratorSetting,
        ExplanationGeneratorSetting
    )

    async def test():
        """Test the QuizGenerationService with mock data"""
        from chromadb import PersistentClient
        from storage.minio import MinioSetting
        from storage.minio import MinioService
        
        minio_setting = MinioSetting(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin123",
            secure=False,
        )
        
        minio_service = MinioService(settings=minio_setting)
        # Setup LiteLLM
        litellm_setting = LiteLLMSetting(
            url=HttpUrl("http://localhost:9510"),
            token=SecretStr("abc123"),
            model="gemini-2.5-flash",
            frequency_penalty=0.0,
            n=1,
            temperature=0.0,
            top_p=1.0,
            max_completion_tokens=10000,
            dimension=1536,
            embedding_model="gemini-embedding"
        )
        litellm_service = LiteLLMService(litellm_setting=litellm_setting)
        
        # Setup individual service settings
        concept_card_setting = ConceptCardExtractorSetting(
            model="gemini-2.5-flash",
            temperature=0.0,
            top_p=1.0,
            n=1,
            frequency_penalty=0.0,
            max_completion_tokens=10000,
        )
        
        topic_generator_setting = TopicGeneratorSetting(
            model="gemini-2.5-flash",
            temperature=0.7,
            top_p=1.0,
            n=1,
            frequency_penalty=0.0,
            max_completion_tokens=10000,
            reasoning_effort="medium"
        )
        
        qa_generator_setting = QuestionAnswerGeneratorSetting(
            model="gemini-2.5-flash",
            temperature=0.5,
            top_p=1.0,
            n=1,
            frequency_penalty=0.0,
            max_completion_tokens=3000,
            reasoning_effort="medium",
            collection_name="questions"
        )
        
        distractors_setting = DistractorsGeneratorSetting(
            model="gemini-2.5-flash",
            temperature=0.7,
            top_p=1.0,
            n=1,
            frequency_penalty=0.0,
            max_completion_tokens=10000,
            reasoning_effort="medium"
        )
        
        explanation_setting = ExplanationGeneratorSetting(
            model="gemini-2.5-flash",
            temperature=0.0,
            top_p=1.0,
            n=1,
            frequency_penalty=0.0,
            max_completion_tokens=10000,
            # reasoning_effort="medium"
        )
        
        quiz_settings = QuizGenerationSetting(
            vector_db_path="/home/vuiem/KLTN/chroma_database",
            max_concurrent_tasks=5,
            concept_card_extractor=concept_card_setting,
            topic_generator=topic_generator_setting,
            question_answer_generator=qa_generator_setting,
            distractors_generator=distractors_setting,
            explanation_generator=explanation_setting
        )
        
        chromadb_client = PersistentClient(path=quiz_settings.vector_db_path)
        # Create main QuizGenerationService
        quiz_generation_service = QuizGenerationService(
            settings=quiz_settings,
            litellm_service=litellm_service,
            minio_service=minio_service,
            chromadb_client=chromadb_client
        )
        
        
        # Test input
        test_input = QuizGenerationInput(
            number_of_topics=7,
            common_mistakes=[],
            week_number=6,
            course_code="int3405"
        )
        
        print("🚀 Starting Quiz Generation Test...")
        print(f"📝 Input: {test_input}")
        print("\n" + "="*50)
        
        try:
            # Process the quiz generation
            output = await quiz_generation_service.process(test_input)
            
            print(f"✅ Quiz Generation Completed!")
            print(f"📊 Generated {len(output.quiz_questions)} quiz questions")
            
            print(f"\n📋 Quiz Questions:")
            for i, question in enumerate(output.quiz_questions, 1):
                print(f"\n--- Question {i} ---")
                print(f"Topic: {question.topic.name}")
                print(f"Difficulty: {question.topic.difficulty_level}")
                print(f"Question: {question.question}")
                print(f"Answer: {question.answer}")
                print(f"Distractors: {len(question.distractors)} items")
                print(f"Has Explanation: {question.explanation.correct_answer_explanation != 'Explanation generation failed'}")
                
            # Save output to file
            output_file = "quiz_generation_test_output.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(output.model_dump(), f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Output saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            logger.exception("Quiz generation test failed", extra={"error": str(e)})
            raise
    
    # Run the test
    asyncio.run(test())


