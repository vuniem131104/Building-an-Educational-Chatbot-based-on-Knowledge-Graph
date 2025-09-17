import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from lite_llm import LiteLLMService
from graph_db import Neo4jService
from storage.minio import MinioService
from fastapi.middleware.cors import CORSMiddleware
from indexing.api.main import router
from indexing.shared.utils import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    app.state.litellm_service = LiteLLMService(
        litellm_setting=app.state.settings.litellm
    )
    app.state.minio_service = MinioService(
        settings=app.state.settings.minio
    )
    app.state.neo4j_service = Neo4jService(
        settings=app.state.settings.neo4j
    )
    
    yield 


app = FastAPI(
    title='Indexing Service',
    description='Service for indexing documents',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3011"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

def main():
    uvicorn.run(
        "indexing:app",
        host='0.0.0.0',
        port=3006,
        log_level='info',
        reload=True,
        workers=2,
    )


