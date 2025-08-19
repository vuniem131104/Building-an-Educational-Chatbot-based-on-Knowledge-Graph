from __future__ import annotations


from base import BaseModel


class PDFSetting(BaseModel):
    threshold: float
    max_concurrent_tasks: int
    dpi: int