from __future__ import annotations 

import os
import base64

from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from base import BaseModel
from base import BaseService
from logger import get_logger

from generation.shared.settings.course_extractor import CourseExtractorSetting
from generation.domain.course_extractor.prompts import COURSE_EXTRACTION_PROMPT 
from generation.domain.parser.docx.utils import convert_docx_to_pdf
from generation.shared.settings.course_extractor import LectureInfo

logger = get_logger(__name__)

class CourseExtractorInput(BaseModel):
    file_path: str
    
class CourseExtractorOutput(BaseModel):
    course_title: str
    course_code: str
    lecture_infos: list[LectureInfo]
    
class CourseExtractorService(BaseService):
    litellm_service: LiteLLMService
    settings: CourseExtractorSetting

    async def process(self, inputs: CourseExtractorInput) -> CourseExtractorOutput:
        """Extract course information from a DOCX file.

        Args:
            inputs (CourseExtractorInput): The input containing the file path.

        Returns:
            CourseExtractorOutput: The extracted course information.
        """
        file_name = os.path.basename(inputs.file_path)
        file_path = inputs.file_path
        os.makedirs(self.settings.upload_folder_path, exist_ok=True)

        try:
            pdf_path = convert_docx_to_pdf(
                input_path=file_path,
                output_dir=self.settings.upload_folder_path
            )
            
            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
            
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=COURSE_EXTRACTION_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            file_url=f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('utf-8')}"
                        )
                    ],
                    response_format=CourseExtractorOutput,
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
                "Error processing DOCX file for course extraction",
                extra={
                    "file_name": file_name,
                    "file_path": file_path,
                    "error": str(e)
                }
            )
            return CourseExtractorOutput(
                course_title="",
                course_code="",
                lecture_infos=[]
            )
            