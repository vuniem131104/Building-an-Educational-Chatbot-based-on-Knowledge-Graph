from __future__ import annotations 

from lite_llm import LiteLLMService
from base import BaseModel
from base import BaseService
from fastapi import UploadFile
import os 
from logger import get_logger

from document.domain.parser.docx import DOCXInput
from document.domain.parser.docx import DOCXService
from document.domain.parser.pdf import PDFInput
from document.domain.parser.pdf import PDFService
from document.domain.parser.pptx import PPTXInput 
from document.domain.parser.pptx import PPTXService
from document.shared.settings import ParserSetting
from document.shared.models import FileType


logger = get_logger(__name__)

class ParserInput(BaseModel):
    file: UploadFile
    
    
class ParserOutput(BaseModel):
    contents: str
    file_name: str 
    

class ParserService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting
    
    @property
    def docx_service(self) -> DOCXService:
        """Get the DOCX service."""
        return DOCXService(
            litellm_service=self.litellm_service,
            settings=self.settings
        )
        
    @property
    def pdf_service(self) -> PDFService:
        """Get the PDF service."""
        return PDFService(
            litellm_service=self.litellm_service,
            settings=self.settings
        )
        
    @property
    def pptx_service(self) -> PPTXService:
        """Get the PPTX service."""
        return PPTXService(
            litellm_service=self.litellm_service,
            settings=self.settings
        )

    async def process(self, inputs: ParserInput) -> ParserOutput:
        os.makedirs(self.settings.upload_folder_path, exist_ok=True)
        os.makedirs(self.settings.image_folder_path, exist_ok=True)
        try:
            inputs.file.file.seek(0)
            file_bytes = await inputs.file.read()
            file_path = os.path.join(self.settings.upload_folder_path, inputs.file.filename)
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            logger.info(
                "Written file successfully",
                extra={
                    "file_name": inputs.file.filename,
                    "file_size": len(file_bytes)
                }
            )
            
            file_type = inputs.file.filename.split('.')[-1].lower()
        
            if file_type == FileType.DOCX or file_type == FileType.DOC:
                docx_input = DOCXInput(file_path=file_path)
                output = await self.docx_service.process(docx_input)
                return ParserOutput(
                    contents=output.contents,
                    file_name=output.file_name,
                )
            
            elif file_type == FileType.PDF:
                pdf_input = PDFInput(file_path=file_path)
                output = await self.pdf_service.process(pdf_input)
                return ParserOutput(
                    contents=output.contents,
                    file_name=output.file_name,
                )

            elif file_type == FileType.PPTX:
                pptx_input = PPTXInput(
                    file_path=file_path,
                )
                output = await self.pptx_service.process(pptx_input)
                return ParserOutput(
                    contents=output.contents,
                    file_name=output.file_name,
                )

            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.exception(
                "Error while processing file",
                extra={
                    "file_name": inputs.file.filename,
                    "error": str(e)
                }
            )
            return ParserOutput(
                contents="",
                file_name=inputs.file.filename
            )
            
            
if __name__ == "__main__":
    import asyncio 
    import io 
    from lite_llm import LiteLLMSetting
    from pydantic import HttpUrl
    from document.shared.settings.parser import PDFSetting
    from document.shared.settings.parser import ImageDesciptorSetting

    service = ParserService(
        litellm_service=LiteLLMService(
            litellm_setting=LiteLLMSetting(
                url=HttpUrl("http://localhost:9510"),
                token="abc123",
                model="gemini-2.5-flash",
                frequency_penalty=0.0,
                n=1,
                temperature=0.0,
                top_p=1.0,
                max_completion_tokens=10000,
            )
        ),
        settings=ParserSetting(
            upload_folder_path="/home/vuiem/KLTN/document/upload",
            image_folder_path="/home/vuiem/KLTN/document/images",
            pdf_settings=PDFSetting(
                threshold=1.0,
                max_concurrent_tasks=5,
                dpi=200,
            ),
            image_descriptor=ImageDesciptorSetting(
                model="gemeni-2.5-flash",
                temperature=0.0,
                top_p=1.0,
                n=1,
                frequency_penalty=0.0,
                max_completion_tokens=1024,
            )
        )
    )
    
    inputs = ParserInput(
        file=UploadFile(
            filename="hehe_anh.pdf",
            file=io.BytesIO(open("/home/vuiem/KLTN/test/files/hehe_anh.pdf", "rb").read())
        )
    )
    
    outputs = asyncio.run(service.process(inputs))
    with open("/home/vuiem/KLTN/test/outputs/output.txt", "w") as f:
        f.write(outputs.contents)


