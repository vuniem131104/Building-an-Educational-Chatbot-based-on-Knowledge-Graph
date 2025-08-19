from __future__ import annotations

import re
import fitz
import os 
import pdfplumber 
import shutil 
import subprocess
from subprocess import run
from typing import List
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)

POWERPOINT_HINTS = (
    'powerpoint', 'mspowerpoint',
    'ppt', 'pptx', 'microsoft powerpoint',
)

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


def should_convert_to_images(pdf_path: str, threshold: float = 1.0) -> bool:
    """
    Analyze PDF content to determine if it should be converted to images or kept as a document.
    
    Args:
        pdf_path (str): the path to the PDF file.
        threshold (float): the threshold for the number of images per page to decide conversion strategy.
    
    Raises:
        ValueError: If the PDF cannot be read.
    
    Returns:
        bool: True if the PDF should be converted to images, False if it can be kept as a document.
    """
    if not os.path.exists(pdf_path):
        raise ValueError(f"PDF file does not exist: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            total_images = 0
            
            for page in pdf.pages:
                if hasattr(page, 'images') and page.images:
                    total_images += len(page.images)
    
    except Exception as e:
        raise ValueError(f"Cannot read PDF: {str(e)}")
    
    # Tính số ảnh trung bình mỗi trang
    images_per_page = total_images / total_pages if total_pages > 0 else 0
    logger.info(f"Total pages: {total_pages}, Total images: {total_images}, Images per page: {images_per_page:.2f}")
    return images_per_page > threshold


def convert_pdf_to_png(pdf_path: str, img_dir: str, dpi: int) -> List[str]:
    """Try to convert PDF to PNG using Ghostscript.

    Args:
        pdf_str (str): str to the PDF file.
        img_dir (str): Directory to save PNG files.
        dpi (int): DPI for the output images.

    Returns:
        List[str]: List of generated PNG files, empty if conversion failed.
    """
    gs = shutil.which('gs')
    if not gs:
        return []

    pattern = Path(img_dir) / 'slide_%03d.png'
    logger.info('Attempting conversion with Ghostscript...')
    try:
        run([
            gs, '-sDEVICE=png16m', f'-r{dpi}',
            '-o', str(pattern), pdf_path,
        ])
        result_files = sorted(Path(img_dir).glob('slide_*.png'))
        if result_files:
            logger.info(f'Ghostscript conversion successful: {len(result_files)} slides')
            return result_files
    except subprocess.CalledProcessError:
        logger.warning('Ghostscript failed, trying next method...')

    return []

