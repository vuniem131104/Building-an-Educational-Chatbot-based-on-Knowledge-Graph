from __future__ import annotations 

import os
import subprocess
import json 
from logger import get_logger
from storage.minio import MinioInput
from storage.minio import MinioService


logger = get_logger(__name__)


def filter_files(files: list[str]) -> list[str]:
    """
    Filters out files that are not in the specified format.
    
    Args:
        files (list[str]): List of file names to filter.
        
    Returns:
        list[str]: Filtered list of file names.
    """
    valid_extensions = {'.pdf', '.pptx'}
    return [file for file in files if any(file.endswith(ext) for ext in valid_extensions)]


def get_lecture_objectives( week_number: int, course_code: str) -> list[str]:
        """Retrieve learning outcomes for the lecture.

        Args:
            week_number (int): The week number.
            course_code (str): The course code.

        Returns:
            list[str]: The learning outcomes for the lecture.
        """

        llo_path = f"/home/vuiem/KLTN/services/generation/src/generation/shared/static_files/{course_code}/learning_outcomes.json"
        with open(llo_path, 'r') as f:
            learning_outcomes = json.load(f)

        week_llo = learning_outcomes.get(f"week_{week_number}", [])

        return week_llo

def get_previous_lectures(minio_service: MinioService, course_code: str, week_number: int) -> list[str]:
        """Retrieve previous lectures' content for quiz generation.

        Args:
            minio_service (MinioService): The Minio service instance.
            course_code (str): The course code.
            week_number (int): The current week number.

        Returns:
            list[str]: List of previous lectures' content.
        """
        previous_lectures: list[str] = []
        
        if week_number == 1:
            logger.info(
                "No previous lectures for week 1",
                extra={
                    "course_code": course_code,
                    "week_number": week_number,
                }
            )
            return []
            
        week_contents: list[str] = []
        for week in range(1, week_number):
            week_contents.append(f"Week {week} content:")
            is_summary_exists = minio_service.check_object_exists(
                MinioInput(
                    bucket_name=course_code, 
                    object_name=f"tuan-{week}/summary.txt"
                )
            )
            if is_summary_exists:
                week_contents.append(
                    minio_service.get_data_from_file(
                        MinioInput(
                            bucket_name=course_code, 
                            object_name=f"tuan-{week}/summary.txt"
                        )
                    )
                )
            else:
                week_contents.append("No summary available for this week.")

        previous_lectures.append("\n".join(week_contents))

        return previous_lectures

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

    