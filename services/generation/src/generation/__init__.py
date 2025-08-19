from __future__ import annotations

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from logger import get_logger
from logger import setup_logging
from lite_llm import LiteLLMService
from storage.minio import MinioService

from generation.api.routers import main_router
from generation.shared.utils import get_settings


setup_logging(json_logs=False, log_level='INFO')
logger = get_logger('api')



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    app.state.litellm_service = LiteLLMService(
        litellm_setting=app.state.settings.litellm
    )
    app.state.minio_service = MinioService(
        settings=app.state.settings.minio
    )
    
    yield 


app = FastAPI(
    title='Generation Service',
    description='Service for generating quizzes and exams',
    version='0.1.0',
    lifespan=lifespan,
)

app.include_router(main_router)

def main():
    uvicorn.run(
        "generation:app",
        host='0.0.0.0',
        port=3006,
        log_level='info',
        reload=True,
    )
