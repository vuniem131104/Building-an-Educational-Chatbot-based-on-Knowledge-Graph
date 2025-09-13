from __future__ import annotations
import os
import io
from pydantic import Field

from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from storage.minio import MinioService 
from storage.minio import MinioInput
from generation.domain.quiz_generation.prompts import CONCEPT_CARDS_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import CONCEPT_CARDS_USER_PROMPT
from generation.shared.settings import ConceptCardExtractorSetting
from generation.domain.parser.pptx.utils import convert_pptx_to_pdf
from generation.shared.models import FileType
from generation.shared.utils import filter_files
from generation.shared.utils import get_previous_lectures
from generation.shared.utils import get_lecture_objectives
import base64
import json
from logger import get_logger

logger = get_logger(__name__)


class ConceptCard(BaseModel):
    name: str = Field(..., description="Concept card title")
    summary: list[str] = Field(..., description="Summary of the concept card content")
    formulae: list[str] = Field(..., description="Formulas related to the concept card")
    examples: list[str] = Field(..., description="Examples illustrating the concept card")
    page: list[int] = Field(..., description="Pages containing the concept card")


class ConceptCards(BaseModel):
    concept_cards: list[ConceptCard] = Field(..., description="List of concept cards extracted from the lecture")
    lecture_summary: str = Field(..., description="Summary of the lecture content")
    

class ConceptCardExtractorInput(BaseModel):
    week_number: int
    course_code: str 
    

class ConceptCardExtractorOutput(BaseModel):
    concept_cards: list[ConceptCard]
    lecture_summary: str
    previous_lectures: list[str]
    lecture_learning_outcomes: list[str]
    week_number: int
    course_code: str
    

class ConceptCardExtractorService(BaseService):
    litellm_service: LiteLLMService
    minio_service: MinioService
    settings: ConceptCardExtractorSetting
    
    async def process(self, inputs: ConceptCardExtractorInput) -> ConceptCardExtractorOutput:
        previous_lectures = get_previous_lectures(
            course_code=inputs.course_code,
            week_number=inputs.week_number,
            minio_service=self.minio_service,
        )
        
        if not previous_lectures:
            logger.warning(
                "No previous lectures found",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                }
            )

        lecture_learning_outcomes = get_lecture_objectives(
            week_number=inputs.week_number,
            course_code=inputs.course_code
        )
        
        if not lecture_learning_outcomes:
            logger.warning(
                "No learning outcomes found for the specified week",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                }
            )
        
        try:
            is_concept_cards_exist = self.minio_service.check_object_exists(
                    MinioInput(
                        bucket_name=inputs.course_code,
                        object_name=f"tuan-{inputs.week_number}/concept_cards.json"
                    )
                )

            if is_concept_cards_exist:
                logger.info(
                    "Concept cards file already exists, skipping processing",
                    extra={
                        "course_code": inputs.course_code,
                        "week_number": inputs.week_number
                    }
                )

                concept_cards_data = self.minio_service.get_data_from_file(
                    MinioInput(
                        bucket_name=inputs.course_code,
                        object_name=f"tuan-{inputs.week_number}/concept_cards.json"
                    )
                )
                
                lecture_summary = self.minio_service.get_data_from_file(
                    MinioInput(
                        bucket_name=inputs.course_code,
                        object_name=f"tuan-{inputs.week_number}/summary.txt"
                    )
                )
                
                return ConceptCardExtractorOutput(
                    concept_cards=[
                        ConceptCard(**card) for card in json.loads(concept_cards_data)
                    ],
                    week_number=inputs.week_number,
                    lecture_summary=lecture_summary,
                    course_code=inputs.course_code,
                    previous_lectures=previous_lectures,
                    lecture_learning_outcomes=lecture_learning_outcomes
                )
        
        except Exception as e:
            logger.exception(
                "Error when checking existing concept cards",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "error": str(e),
                } 
            )
                
        try:
            folder_path = f"{inputs.course_code}/tuan-{inputs.week_number}"
            os.makedirs(folder_path, exist_ok=True)
            files = self.minio_service.list_files(
                bucket_name=inputs.course_code, 
                prefix=f"tuan-{inputs.week_number}/",
                recursive=False
            )
            
            filtered_files = filter_files(files)
            
            if not filtered_files:
                logger.error(
                    'No files found for quiz generation',
                    extra={
                        'course_code': inputs.course_code,
                        'week_number': inputs.week_number,
                    },
                )
                
                raise ValueError("No files found for quiz generation")
                
            # only process the first file for concept card extraction
            file = filtered_files[0]
            file_path = f"{inputs.course_code}/{file}"
            filename = file_path.split('/')[-1]
            
            _ = self.minio_service.download_file(
                MinioInput(
                    bucket_name=inputs.course_code, 
                    object_name=file,
                    file_path=file_path
                )
            )
        
            file_type = filename.split('.')[-1].lower()
            
            if file_type == FileType.PPTX:
                pdf_path = convert_pptx_to_pdf(
                    input_path=file_path,
                    output_dir=inputs.course_code
                )
            elif file_type == FileType.PDF:
                pdf_path = file_path
            else:
                logger.error(
                    "Unsupported file type for concept card extraction",
                    extra={
                        "course_code": inputs.course_code,
                        "week_number": inputs.week_number,
                        "file_name": filename
                    }
                )
                raise ValueError("Unsupported file type for concept card extraction")
            
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                
        except Exception as e:
            logger.exception(
                "Error when downloading and processing files",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "error": str(e),
                } 
            )
            raise e
        
        try:
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    model=self.settings.model,
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=CONCEPT_CARDS_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=CONCEPT_CARDS_USER_PROMPT,
                            file_url=f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('utf-8')}"
                        )
                    ],
                    response_format=ConceptCards,
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                    reasoning_effort=self.settings.reasoning_effort,
                )
            )
            
            concept_cards = output.response.concept_cards
            lecture_summary = output.response.lecture_summary
            
            _ = self.minio_service.upload_data(
                MinioInput(
                    bucket_name=inputs.course_code,
                    object_name=f"tuan-{inputs.week_number}/concept_cards.json",
                    data=io.BytesIO(json.dumps([concept_card.model_dump() for concept_card in concept_cards], ensure_ascii=False).encode('utf-8'))
                )
            )
            
            _ = self.minio_service.upload_data(
                MinioInput(
                    bucket_name=inputs.course_code,
                    object_name=f"tuan-{inputs.week_number}/summary.txt",
                    data=io.BytesIO(lecture_summary.encode('utf-8'))
                )
            )

            logger.info(
                "Concept cards extracted and uploaded successfully",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "num_concept_cards": len(concept_cards)
                }
            )

            return ConceptCardExtractorOutput(
                concept_cards=concept_cards,
                lecture_summary=lecture_summary,
                week_number=inputs.week_number,
                course_code=inputs.course_code,
                previous_lectures=previous_lectures,
                lecture_learning_outcomes=lecture_learning_outcomes,
            )

        except Exception as e:
            logger.exception(
                "Error when processing concept card extraction with litellm",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "error": str(e),
                } 
            )
            raise e
    
if __name__ == "__main__":
    from lite_llm import LiteLLMSetting
    from storage.minio import MinioSetting
    import asyncio
    from pydantic import HttpUrl, SecretStr

    litellm_setting=LiteLLMSetting(
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
    
    minio_setting = MinioSetting(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False,
    )
    
    settings = ConceptCardExtractorSetting(
        model="gemini-2.5-flash",
        temperature=0.0,
        top_p=1.0,
        n=1,
        frequency_penalty=0.0,
        max_completion_tokens=10000,
    )

    litellm_service = LiteLLMService(litellm_setting=litellm_setting)
    minio_service = MinioService(settings=minio_setting)
    concept_card_extractor_service = ConceptCardExtractorService(
        litellm_service=litellm_service,
        minio_service=minio_service,
        settings=settings
    )

    async def test():
        output = await concept_card_extractor_service.process(
            inputs=ConceptCardExtractorInput(
                week_number=6,
                course_code="int3405"
            )
        )
        print(output)

    asyncio.run(test())