from __future__ import annotations

import asyncio
import os
from base import BaseService
from base import BaseModel
from logger import get_logger
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from generation.domain.exam_generation.prompts import TOPIC_SYSTEM_PROMPT, TOPIC_USER_PROMPT, QUESTION_GENERATION_SYSTEM_PROMPT, QUESTION_GENERATION_USER_PROMPT, COURSE_CONTENT_TEMPLATE
from generation.shared.models import GenerationType
from generation.shared.models import Questions
from generation.shared.models import Question
from generation.shared.settings import ExamGenerationSetting
from storage.minio import MinioInput
from storage.minio import MinioService
import chromadb.utils.embedding_functions as embedding_functions
import chromadb
from dotenv import load_dotenv


logger = get_logger(__name__)

class Slot(BaseModel):
    type: str 
    target_weeks: list[int] 
    difficulty: str 
    topic_description: str
    
class Slots(BaseModel):
    topics: list[Slot]

class ExamGenerationInput(BaseModel):
    course_code: str
    generation_type: GenerationType = GenerationType.MULTIPLE_CHOICE
    num_questions: int
    num_multiple_choice: int = 0
    num_essay: int = 0
    num_case_study: int = 0
    start_week: int
    end_week: int
    
    

class ExamGenerationOutput(BaseModel):
    start_week: int
    end_week: int
    course_code: str
    questions: Questions


class ExamGenerationService(BaseService):

    exam_settings: ExamGenerationSetting
    litellm_service: LiteLLMService
    minio_service: MinioService
    
    @property
    def chroma_client(self):
        return chromadb.PersistentClient(path=self.exam_settings.chroma_db)

    @property
    def embedding(self):
        return embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=os.getenv("GEMINI_API_KEY1"))

    async def process(self, inputs: ExamGenerationInput) -> ExamGenerationOutput:
        """Generate exam questions based on the input type and number of questions.

        Args:
            inputs (ExamGenerationInput): The input containing generation type and number of questions.

        Returns:
            ExamGenerationOutput: The generated exam questions.
        """
        formatted_objectives = 'Here are the objectives for each week:\n'
        for week_number in range(inputs.start_week, inputs.end_week + 1):
            week_objectives = self.minio_service.get_data_from_file(
                    input=MinioInput(
                        bucket_name=inputs.course_code,
                        object_name=f"tuan-{week_number}/objectives.json"
                    )
                )
            formatted_objectives += f"Week {week_number}: {'\n'.join(week_objectives)}\n"
            
        if inputs.generation_type == GenerationType.MULTIPLE_CHOICE:
            blueprint = {
                'mcq': inputs.num_questions,
                'short_answer': 0,
                'case_study': 0,
            }
        elif inputs.generation_type == GenerationType.ESSAY:
            blueprint = {
                'mcq': 0,
                'short_answer': inputs.num_questions,
                'case_study': 0,
            }
        elif inputs.generation_type == GenerationType.MIXED:
            blueprint = {
                'mcq': inputs.num_multiple_choice,
                'short_answer': inputs.num_essay,
                'case_study': inputs.num_case_study,
            }
            
        slots = await self.litellm_service.process_async(
            inputs=LiteLLMInput(
                model="gemini-2.5-flash",
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content=TOPIC_SYSTEM_PROMPT
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=TOPIC_USER_PROMPT.format(
                            num_mcq=blueprint['mcq'],
                            num_short_answer=blueprint['short_answer'],
                            num_case_study=blueprint['case_study'],
                            total_questions=blueprint['mcq'] + blueprint['short_answer'] + blueprint['case_study'],
                            formatted_objectives=formatted_objectives
                        )
                    )
                ],
                response_format=Slots,
                temperature=self.exam_settings.temperature,
                top_p=self.exam_settings.top_p,
                n=self.exam_settings.n,
                frequency_penalty=self.exam_settings.frequency_penalty,
                max_completion_tokens=self.exam_settings.max_completion_tokens,
                reasoning_effort=self.exam_settings.reasoning_effort,
            )
        )
        
        semaphore = asyncio.Semaphore(self.exam_settings.max_concurrent_tasks)
        
        async def process_with_semaphore(slot: Slot):
            async with semaphore:
                query = slot.topic_description 
                
                embeddings = self.embedding([query])
                collection = self.chroma_client.get_collection(self.exam_settings.collection)
                results = collection.query(
                    query_embeddings=embeddings,
                    n_results=3,
                    where={"week": {"$in": slot.target_weeks}}
                )
                
                course_content = ""
                if results["documents"] and len(results["documents"]) > 0:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] and len(results["metadatas"][0]) > i else {}
                        course_content += COURSE_CONTENT_TEMPLATE.format(
                            doc_number=i+1,
                            doc_content=doc,
                            name=metadata.get('name', ''),
                            week=metadata.get('week', ''),
                            formulae=metadata.get('formulae', ''),
                            example=metadata.get('example', ''),
                            common_pitfalls=metadata.get('common_pitfalls', '')
                        )
                            
                logger.info(
                    'Course content for {}'.format(slot.topic_description),
                    extra={
                        'course_content': course_content,
                    }
                )
                
                question_response = await self.litellm_service.process_async(
                    inputs=LiteLLMInput(
                        model="gemini-2.5-flash",
                        messages=[
                            CompletionMessage(
                                role=Role.SYSTEM,
                                content=QUESTION_GENERATION_SYSTEM_PROMPT
                            ),
                            CompletionMessage(
                                role=Role.USER,
                                content=QUESTION_GENERATION_USER_PROMPT.format(
                                    question_type=slot.type,
                                    difficulty=slot.difficulty,
                                    topic_description=slot.topic_description,
                                    target_weeks=slot.target_weeks,
                                    course_content=course_content
                                )
                            )
                        ],
                        response_format=Question,
                        temperature=self.exam_settings.temperature,
                        top_p=self.exam_settings.top_p,
                        n=self.exam_settings.n,
                        frequency_penalty=self.exam_settings.frequency_penalty,
                        max_completion_tokens=self.exam_settings.max_completion_tokens,
                        reasoning_effort=self.exam_settings.reasoning_effort,
                    )
                )
                
                return question_response.response
        
        tasks = [process_with_semaphore(slot) for slot in slots.response.topics]
        generated_questions = await asyncio.gather(*tasks)
        
        all_questions = []
        for question_response in generated_questions:
            all_questions.append(question_response)
        
        return ExamGenerationOutput(
            start_week=inputs.start_week,
            end_week=inputs.end_week,
            course_code=inputs.course_code,
            questions=Questions(questions=all_questions)
        )