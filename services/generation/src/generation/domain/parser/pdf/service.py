from __future__ import annotations

import os
import base64
import shutil
import asyncio

from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from base import BaseModel
from base import BaseService
from generation.shared.settings import ParserSetting
from logger import get_logger

from generation.domain.parser.pdf.prompts import PDF_SYSTEM_PROMPT
from generation.domain.parser.pdf.utils import should_convert_to_images
from generation.domain.parser.pdf.utils import convert_pdf_to_png
from generation.domain.parser.pdf.utils import is_powerpoint_pdf
from generation.domain.parser.image_descriptor import ImageDescriptorService
from generation.domain.parser.image_descriptor import ImageDescriptorInput
from generation.domain.parser.image_descriptor import ImageDescriptorOutput


logger = get_logger(__name__)


class PDFInput(BaseModel):
    file_path: str


class PDFOutput(BaseModel):
    contents: str
    file_name: str


class PDFService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting
    
    @property
    def image_descriptor_service(self) -> ImageDescriptorService:
        """Get the image descriptor service."""
        return ImageDescriptorService(
            litellm_service=self.litellm_service,
            settings=self.settings,
        )

    async def process(self, inputs: PDFInput) -> PDFOutput:
        """Process the PDF file and extract contents.

        Args:
            inputs (PDFInput): The input containing the file path.

        Returns:
            PDFOutput: The processed output containing contents and file name.
        """
        file_name = os.path.basename(inputs.file_path)
        file_path = inputs.file_path
        img_dir = os.path.join(self.settings.image_folder_path, file_name.split('.')[0])
        os.makedirs(img_dir, exist_ok=True)

        try:
            is_pptx = is_powerpoint_pdf(file_path)
            if not is_pptx:
                logger.info(
                    "Processing original PDF file",
                )
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()

                output = await self.litellm_service.process_async(
                    inputs=LiteLLMInput(
                        messages=[
                            CompletionMessage(
                                role=Role.SYSTEM,
                                content=PDF_SYSTEM_PROMPT
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
            else:
                logger.info(
                    "This file is a PowerPoint PDF, checking if it should be converted to images",
                )
                should_convert = should_convert_to_images(file_path, self.settings.pdf_settings.threshold)
                if not should_convert:
                    logger.info(
                        "Processing PowerPoint PDF file without conversion",
                    )
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()

                    output = await self.litellm_service.process_async(
                        inputs=LiteLLMInput(
                            messages=[
                                CompletionMessage(
                                    role=Role.SYSTEM,
                                    content=PDF_SYSTEM_PROMPT
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
                else:
                    logger.info(
                        "Converting PowerPoint PDF to images",
                    )
                    _ = convert_pdf_to_png(
                        pdf_path=file_path,
                        img_dir=img_dir,
                        dpi=self.settings.pdf_settings.dpi
                    )
                    
                    semaphore = asyncio.Semaphore(self.settings.pdf_settings.max_concurrent_tasks)

                    async def process_with_semaphore(file_path: str):
                        async with semaphore:
                            return await self.image_descriptor_service.process(
                                inputs=ImageDescriptorInput(
                                    file_path=file_path,
                                )
                            )

                    tasks = [
                        process_with_semaphore(file_path=os.path.join(img_dir, _file_name))
                        for _file_name in os.listdir(img_dir)
                    ]
                    raw_contents = await asyncio.gather(*tasks)
                    sorted_contents = self._sort_contents(raw_contents)

                    contents = f'# File title (Slide 1): {sorted_contents[0][0]}\n\n'

                    for content, num_slide in sorted_contents[1:]:
                        contents += f'## Slide {num_slide} content: \n\n{content}\n\n'

                    return PDFOutput(
                        contents=contents,
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
            self._delete_files_and_images(file_path, img_dir)

    def _delete_files_and_images(self, file_path: str, img_dir: str):
        """Delete temporary files and images created during processing.

        Args:
            file_path (str): The path to the file to delete.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.exception(f"Error deleting file {file_path}: {str(e)}")

        try:
            shutil.rmtree(img_dir)
            logger.info(f"Deleted directory and all images: {img_dir}")
        except Exception as e:
            logger.exception(f"Error deleting directory {img_dir}: {str(e)}")

    def _sort_contents(self, image_outputs: list[ImageDescriptorOutput]) -> list[tuple[str, int]]:
        """Sort image outputs by slide number.

        Args:
            image_outputs (list[ImageDescriptorOutput]): List of image descriptor outputs.

        Returns:
            list[tuple[str, int]]: Sorted list of tuples containing slide content and slide number.
        """
        return sorted(
            [(output.image_content, int(output.file_name.split('_')[-1].split('.')[0])) for output in image_outputs],
            key=lambda x: x[1]
        )
