from __future__ import annotations

import re
import fitz
from logger import get_logger

logger = get_logger(__name__)

SLIDE_ASPECT_RATIOS = {
    16 / 9,
    4 / 3,
}

def is_powerpoint_pdf(path: str) -> bool:
    """Check if a PDF file likely came from a PowerPoint export using PyMuPDF.
    Args:
        path (str): Path to the PDF file.
    Returns:
        bool: True if the PDF is likely from PowerPoint, False otherwise.
    """
    doc = fitz.open(path)
    try:
        meta_text = ' '.join(str(v).lower() for v in doc.metadata.values())
        if any(k in meta_text for k in ('powerpoint', 'ppt')):
            return True

        # Check page 1 (index 0) for aspect ratio
        w_in, h_in = doc[0].rect.width / 72, doc[0].rect.height / 72

        # Calculate aspect ratio
        aspect_ratio = w_in / h_in

        # Check if aspect ratio matches PowerPoint standards (with tolerance)
        for target_ratio in SLIDE_ASPECT_RATIOS:
            tolerance = 0.1
            if abs(aspect_ratio - target_ratio) <= tolerance:
                logger.info(f'Aspect ratio {aspect_ratio:.3f} matches PowerPoint ratio {target_ratio:.3f}')
                return True

        try:
            lbl0 = doc.get_page_label(0).lower()
            if re.fullmatch(r'slide[\s\-]*0*1', lbl0):
                return True
        except (KeyError, AttributeError):
            pass
        return False
    finally:
        doc.close()