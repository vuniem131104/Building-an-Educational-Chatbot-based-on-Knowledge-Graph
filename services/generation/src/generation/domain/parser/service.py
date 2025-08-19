from __future__ import annotations 


from storage.minio import MinioService
from storage.minio import MinioInput
from lite_llm import LiteLLMService
from base import BaseModel
from base import BaseService
import os 
import io 
from logger import get_logger

from generation.domain.parser.docx import DOCXInput
from generation.domain.parser.docx import DOCXService
from generation.domain.parser.pdf import PDFInput
from generation.domain.parser.pdf import PDFService
from generation.domain.parser.pptx import PPTXInput 
from generation.domain.parser.pptx import PPTXService
from generation.shared.settings import ParserSetting
from generation.shared.models import FileType
from generation.shared.utils import filter_files


logger = get_logger(__name__)

class ParserInput(BaseModel):
    course_code: str 
    week_number: int
    
    
class ParserOutput(BaseModel):
    contents: str
    course_code: str
    week_number: int
    

class ParserService(BaseService):
    litellm_service: LiteLLMService
    minio_service: MinioService
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
        folder_path = f"{inputs.course_code}/tuan-{inputs.week_number}"
        os.makedirs(folder_path, exist_ok=True)
        try:
            contents: list[str] = []
            files = self.minio_service.list_files(
                bucket_name=inputs.course_code, 
                prefix=f"tuan-{inputs.week_number}/",
                recursive=False
            )
            
            filtered_files = filter_files(files)
            
            if not filtered_files:
                logger.warning(
                    'No files found for quiz generation',
                    extra={
                        'course_code': inputs.course_code,
                        'week_number': inputs.week_number,
                    },
                )
                
                return ParserOutput(
                    contents="",
                    course_code=inputs.course_code,
                    week_number=inputs.week_number,
                )
                
            for file in filtered_files:
                file_path = f"{inputs.course_code}/{file}"
                filename = file_path.split('/')[-1]
                
                is_parser_exist = self.minio_service.check_object_exists(
                    MinioInput(
                        bucket_name=inputs.course_code,
                        object_name=f"tuan-{inputs.week_number}/{filename.split('.')[0]}_parser.txt"
                    )
                )
                
                if is_parser_exist:
                    logger.info(
                        "Parser file already exists, skipping processing",
                        extra={
                            "file_name": filename,
                            "course_code": inputs.course_code,
                            "week_number": inputs.week_number
                        }
                    )
                    
                    contents.append(
                        self.minio_service.get_data_from_file(
                            MinioInput(
                                bucket_name=inputs.course_code,
                                object_name=f"tuan-{inputs.week_number}/{filename.split('.')[0]}_parser.txt"
                            )
                        )
                    )
                        
                    continue
                
                _ = self.minio_service.download_file(
                    MinioInput(
                        bucket_name=inputs.course_code, 
                        object_name=file,
                        file_path=file_path
                    )
                )
            
                file_type = filename.split('.')[-1].lower()
            
                if file_type == FileType.DOCX or file_type == FileType.DOC:
                    docx_input = DOCXInput(file_path=file_path)
                    output = await self.docx_service.process(docx_input)
                    
                
                elif file_type == FileType.PDF:
                    pdf_input = PDFInput(file_path=file_path)
                    output = await self.pdf_service.process(pdf_input)
                    

                elif file_type == FileType.PPTX:
                    pptx_input = PPTXInput(
                        file_path=file_path,
                    )
                    output = await self.pptx_service.process(pptx_input)
                
                contents.append(output.contents)
                    
                _ = self.minio_service.upload_data(
                        MinioInput(
                            bucket_name=inputs.course_code,
                            object_name=f"tuan-{inputs.week_number}/{filename.split('.')[0]}_parser.txt",
                            data=io.BytesIO(output.contents.encode('utf-8'))
                        )
                    )
                
            return ParserOutput(
                contents="\n".join(contents),
                course_code=inputs.course_code,
                week_number=inputs.week_number,
            )
            
        except Exception as e:
            logger.exception(
                "Error while processing file",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "error": str(e)
                }
            )
            return ParserOutput(
                contents="",
                course_code=inputs.course_code,
                week_number=inputs.week_number,
            )
