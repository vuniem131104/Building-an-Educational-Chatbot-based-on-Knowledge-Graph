from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from lite_llm import LiteLLMSetting
from graph_db import Neo4jSetting
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import YamlConfigSettingsSource  # type: ignore

from .local_search import LocalSearchSettings

# test in local
load_dotenv()


class Settings(BaseSettings):
    neo4j: Neo4jSetting
    litellm: LiteLLMSetting
    local_search_settings: LocalSearchSettings

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
