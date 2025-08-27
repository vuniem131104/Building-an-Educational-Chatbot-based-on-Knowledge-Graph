from __future__ import annotations

from enum import Enum

class FileType(str, Enum):
    PDF = 'pdf'
    PPTX = 'pptx'