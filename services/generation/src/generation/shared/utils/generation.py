from __future__ import annotations 

from typing import Any 
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
    
    