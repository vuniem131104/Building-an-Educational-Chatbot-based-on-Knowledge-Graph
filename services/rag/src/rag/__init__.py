import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from lite_llm import LiteLLMService
from graph_db import Neo4jService

from rag.api.main import router
from rag.shared.utils import get_settings




@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    app.state.litellm_service = LiteLLMService(
        litellm_setting=app.state.settings.litellm
    )
    app.state.neo4j_service = Neo4jService(
        settings=app.state.settings.neo4j
    )
    
    yield 


app = FastAPI(
    title='RAG Service',
    description='Service for retrieving relevant information',
    version='0.1.0',
    lifespan=lifespan,
)

app.include_router(router)

def main():
    uvicorn.run(
        "rag:app",
        host='0.0.0.0',
        port=3005,
        log_level='info',
        reload=True,
    )


