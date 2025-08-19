import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from lite_llm import LiteLLMService
from fastapi.middleware.cors import CORSMiddleware
from chatbot.api.main import router
from chatbot.shared.utils import get_settings
from pg import SQLDatabase

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    app.state.litellm_service = LiteLLMService(
        litellm_setting=app.state.settings.litellm
    )
    app.state.database_service = SQLDatabase(
        username=os.getenv('POSTGRES__USERNAME'),
        password=os.getenv('POSTGRES__PASSWORD'),
        db=os.getenv('POSTGRES__DB'),
        host=os.getenv('POSTGRES__HOST'),
        port=os.getenv('POSTGRES__PORT'),
    )
    
    yield 


app = FastAPI(
    title='Chatbot Service',
    description='Service for chatbot interactions',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3011", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

def main():
    uvicorn.run(
        "chatbot:app",
        host='0.0.0.0',
        port=3010,
        log_level='info',
        reload=True,
    )


