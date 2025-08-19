from __future__ import annotations

import base64

from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput 
from lite_llm import CompletionMessage
from lite_llm import Role
from base import BaseModel
from base import BaseService
from logger import get_logger


from generation.shared.settings import ParserSetting
from generation.domain.parser.image_descriptor.prompts import PPTX_SYSTEM_PROMPT
from generation.domain.parser.image_descriptor.prompts import FIRST_SLIDE_SYSTEM_PROMPT


logger = get_logger(__name__)


class ImageDescriptorInput(BaseModel):
    file_path: str


class ImageDescriptorOutput(BaseModel):
    image_content: str
    file_name: str


class ImageDescriptorService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting

    async def process(self, inputs: ImageDescriptorInput) -> ImageDescriptorOutput:
        """Process the image file and extract contents.

        Args:
            inputs (ImageDescriptorInput): The input containing the file path.

        Returns:
            ImageDescriptorOutput: The processed output containing image content and file name.
        """
        
        try:
            filename = inputs.file_path.split('/')[-1]
            num_slide = int(filename.split('.')[0].split('_')[-1])
            with open(inputs.file_path, 'rb') as image_file:
                b64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            logger.info(
                "Processing image file",
                extra={
                    "file_path": inputs.file_path,
                    "num_slide": num_slide,
                    "length": len(b64)
                }
            )
                
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=FIRST_SLIDE_SYSTEM_PROMPT if num_slide == 1 else PPTX_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            image_url=f"data:image/png;base64,{b64}"
                        )
                    ],
                    model=self.settings.image_descriptor.model,
                    temperature=self.settings.image_descriptor.temperature,
                    top_p=self.settings.image_descriptor.top_p,
                    n=self.settings.image_descriptor.n,
                    frequency_penalty=self.settings.image_descriptor.frequency_penalty,
                    max_completion_tokens=self.settings.image_descriptor.max_completion_tokens,
                )
            )
            return ImageDescriptorOutput(
                image_content=output.response,
                file_name=filename
            )
        except Exception as e:
            logger.exception(
                "Error processing image file",
                extra={
                    "error": str(e),
                    "file_path": inputs.file_path,
                }
            )
            return ImageDescriptorOutput(
                image_content="",
                file_name=inputs.file_path.split('/')[-1]
            )