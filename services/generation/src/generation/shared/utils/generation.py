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
    valid_extensions = {'.pdf', '.docx', '.doc', '.pptx'}
    return [file for file in files if any(file.endswith(ext) for ext in valid_extensions)]


def get_lecture_learning_outcomes(minio_service: MinioService, course_code: str) -> dict[str, Any]:
        """Retrieve learning outcomes for the lecture.

        Args:
            minio_service (MinioService): The Minio service instance.
            course_code (str): The course code.

        Returns:
            dict[str, Any]: The learning outcomes for the lecture.
        """
        
        is_exists = minio_service.check_object_exists(
            MinioInput(
                bucket_name=course_code, 
                object_name=f"{course_code}.json"
            )
        )
        if not is_exists:
            logger.warning(
                'Learning outcomes file not found',
                extra={
                    'course_code': course_code,
                }
            )
            return {}

        return json.loads(
            minio_service.get_data_from_file(
                MinioInput(
                    bucket_name=course_code, 
                    object_name=f"{course_code}.json"
                )
            )
        )
    
def get_week_learning_outcomes(week_number, learning_outcomes: dict[str, Any]) -> tuple[str, str]:
    """Retrieve learning outcomes for the specific week.

    Args:
        week_number (int): The week number.
        learning_outcomes (dict[str, Any]): The learning outcomes for the lecture.

    Returns:
        tuple[str, str]: The introduction and learning outcomes for the week.
    """
    lecture_infos = learning_outcomes.get('lecture_infos', [])
    if not lecture_infos or len(lecture_infos) < week_number:
        return "No introduction provided.", "No learning outcomes provided."
    return lecture_infos[week_number - 1].get('introduction', ''), "\n".join(lecture_infos[week_number - 1].get('lecture_learning_outcomes', ["No learning outcomes provided."]))


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

        logger.info(
            "Previous lectures content",
            extra={
                "previous_lectures": previous_lectures,
            }
        )

        return previous_lectures
    
    