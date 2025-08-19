from __future__ import annotations

import os
from lite_llm import LiteLLMService
from base import BaseModel
from base import BaseService
from logger import get_logger

from generation.shared.settings import ParserSetting
from generation.domain.parser.pptx.utils import convert_pptx_to_pdf
from generation.domain.parser.pdf import PDFInput
from generation.domain.parser.pdf import PDFService


logger = get_logger(__name__)


class PPTXInput(BaseModel):
    file_path: str


class PPTXOutput(BaseModel):
    contents: str
    file_name: str


class PPTXService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting

    @property
    def pdf_service(self) -> PDFService:
        """Get the PDF service."""
        return PDFService(
            litellm_service=self.litellm_service,
            settings=self.settings
        )

    async def process(self, inputs: PPTXInput) -> PPTXOutput:
        """Process the PPTX file and extract contents.

        Args:
            inputs (PPTXInput): The input containing the file path.

        Returns:
            PPTXOutput: The processed output containing contents and positions.
        """
        file_name = os.path.basename(inputs.file_path)
        file_path = inputs.file_path

        try:
            pdf_path = convert_pptx_to_pdf(
                input_path=file_path,
                output_dir=self.settings.upload_folder_path
            )
            
            pdf_input = PDFInput(file_path=pdf_path)
            pdf_output = await self.pdf_service.process(pdf_input)
            
            return PPTXOutput(
                contents=pdf_output.contents,
                file_name=file_name,
            )
        except Exception as e:
            logger.exception(
                'Error processing PPTX file',
                extra={
                    'file_name': file_name,
                    'file_path': file_path,
                    'error': str(e),
                },
            )
            return PPTXOutput(
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