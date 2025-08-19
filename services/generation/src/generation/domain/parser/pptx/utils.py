from __future__ import annotations

import os
import subprocess
from logger import get_logger

logger = get_logger(__name__)

def convert_pptx_to_pdf(input_path: str, output_dir: str = None):
    """
    Convert a PPTX file to PDF using LibreOffice.

    Args:
        input_path (str): Path to the .pptx file.
        output_dir (str, optional): Directory to save the .pdf file. 
                                    If None, saves to the same directory as the input file.

    Returns:
        str: Path to the output PDF file if successful, None if an error occurs.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    logger.info(f"Converting {input_path} to PDF...")

    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path]
    if output_dir:
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        cmd.extend(["--outdir", output_dir])

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        logger.error(f"Error converting file: {result.stderr.decode('utf-8')}")
        return None

    filename = os.path.basename(input_path)
    pdf_name = os.path.splitext(filename)[0] + ".pdf"
    output_path = os.path.join(output_dir or os.path.dirname(input_path), pdf_name)
    
    if os.path.exists(output_path):
        logger.info(f"Successfully converted pptx to pdf: {output_path}")
        return output_path
    else:
        logger.error("PDF conversion reported success, but output file not found.")
        return None
