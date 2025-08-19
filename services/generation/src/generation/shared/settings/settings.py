from __future__ import annotations

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import YamlConfigSettingsSource
from pathlib import Path

from lite_llm import LiteLLMSetting
from storage.minio import MinioSetting
from .quiz_settings import QuizGenerationSetting
from .exam_settings import ExamGenerationSetting
from .course_extractor import CourseExtractorSetting
from .lecture_summarizer import LectureSummarizerSetting
from .quiz_validator import QuizValidatorSetting
from .parser import ParserSetting

load_dotenv()


class Settings(BaseSettings):
    
    lecture_summarizer: LectureSummarizerSetting
    parser: ParserSetting
    quiz: QuizGenerationSetting
    exam: ExamGenerationSetting
    litellm: LiteLLMSetting
    minio: MinioSetting
    course_extractor: CourseExtractorSetting
    
    quiz_validator: QuizValidatorSetting

    class Config:
        env_nested_delimiter = '__'
        yaml_file = str(Path(__file__).parent.parent.parent / 'settings.yaml')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )
