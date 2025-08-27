from __future__ import annotations

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import YamlConfigSettingsSource
from pathlib import Path

from lite_llm import LiteLLMSetting
from graph_db import Neo4jSetting
from storage.minio import MinioSetting
from .parser import ParserSetting
from .chunker import ChunkerSetting
from .redis import RedisSetting

load_dotenv()


class Settings(BaseSettings):
    
    parser: ParserSetting
    litellm: LiteLLMSetting
    minio: MinioSetting
    chunker: ChunkerSetting
    neo4j: Neo4jSetting
    redis: RedisSetting

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
