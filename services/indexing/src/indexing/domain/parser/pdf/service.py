from __future__ import annotations

import os
import base64
import shutil

from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from base import BaseModel
from base import BaseService
from indexing.shared.settings.parser import ParserSetting
from logger import get_logger

from indexing.domain.parser.pdf.prompts import PDF_SYSTEM_PROMPT
from indexing.domain.parser.pdf.prompts import PDF_SYSTEM_PROMPT_PPTX
from indexing.domain.parser.pdf.utils import is_powerpoint_pdf

logger = get_logger(__name__)


class PDFInput(BaseModel):
    file_path: str


class PDFOutput(BaseModel):
    contents: str
    file_name: str


class PDFService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting
    
    async def process(self, inputs: PDFInput) -> PDFOutput:
        """Process the PDF file and extract contents.

        Args:
            inputs (PDFInput): The input containing the file path.

        Returns:
            PDFOutput: The processed output containing contents and file name.
        """
        file_name = os.path.basename(inputs.file_path)
        file_path = inputs.file_path

        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
                
            is_pptx = is_powerpoint_pdf(file_path)

            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=PDF_SYSTEM_PROMPT if not is_pptx else PDF_SYSTEM_PROMPT_PPTX
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            file_url=f"data:application/pdf;base64,{base64.b64encode(file_bytes).decode('utf-8')}"
                        )
                    ]
                )
            )

            return PDFOutput(
                contents=output.response,
                file_name=file_name,
            )
        except Exception as e:
            logger.exception(
                'Error processing PDF file',
                extra={
                    'file_name': file_name,
                    'file_path': file_path,
                    'error': str(e),
                },
            )
            return PDFOutput(
                contents="",
                file_name=file_name,
            )
            
        finally:
            self._delete_files(file_path)

    def _delete_files(self, file_path: str):
        """Delete temporary files created during processing.

        Args:
            file_path (str): The path to the file to delete.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.exception(f"Error deleting file {file_path}: {str(e)}")

