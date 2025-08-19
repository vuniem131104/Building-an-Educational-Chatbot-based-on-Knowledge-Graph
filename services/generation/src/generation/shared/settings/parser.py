from __future__ import annotations

from base import BaseModel 
from .image_descriptor import ImageDesciptorSetting
from .pdf_settings import PDFSetting


class ParserSetting(BaseModel):
    upload_folder_path: str
    image_folder_path: str
    pdf_settings: PDFSetting
    image_descriptor: ImageDesciptorSetting

