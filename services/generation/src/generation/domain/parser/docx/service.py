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

from generation.shared.settings import ParserSetting
from generation.domain.parser.docx.prompts import DOCX_SYSTEM_PROMPT
from generation.domain.parser.docx.utils import convert_docx_to_pdf


logger = get_logger(__name__)


class DOCXInput(BaseModel):
    file_path: str


class DOCXOutput(BaseModel):
    contents: str
    file_name: str


class DOCXService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting

    async def process(self, inputs: DOCXInput) -> DOCXOutput:
        """Process the DOCX file and extract contents.

        Args:
            inputs (DOCXInput): The input containing the file path.

        Returns:
            DOCXOutput: The processed output containing contents and file name.
        """
        file_name = os.path.basename(inputs.file_path)
        file_path = inputs.file_path

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
                            content=DOCX_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            file_url=f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('utf-8')}"
                        )
                    ]
                )
            )
            
            return DOCXOutput(
                contents=output.response,
                file_name=file_name,
            )
        except Exception as e:
            logger.exception(
                'Error processing DOCX file',
                extra={
                    'file_name': file_name,
                    'file_path': file_path,
                    'error': str(e),
                },
            )
            return DOCXOutput(
                contents="",
                file_name=file_name,
            )
        finally:
            self._delete_files(file_path)
            self._delete_files(pdf_path)
            
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