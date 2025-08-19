from __future__ import annotations

from base import BaseModel 


class ImageDesciptorSetting(BaseModel):
    model: str 
    temperature: float
    top_p: float
    n: int
    frequency_penalty: float
    max_completion_tokens: int
    
class PDFSetting(BaseModel):
    threshold: float
    max_concurrent_tasks: int
    dpi: int

class ParserSetting(BaseModel):
    upload_folder_path: str
    image_folder_path: str
    pdf_settings: PDFSetting
    image_descriptor: ImageDesciptorSetting

