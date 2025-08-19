from chatbot.application import ChatbotApplication 
from chatbot.application import ChatbotApplicationInput 
from fastapi import BackgroundTasks, Request 
from fastapi import APIRouter
from fastapi.responses import JSONResponse 
from base import BaseModel
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1")

class ChatbotRequest(BaseModel):
    question: str

@router.post("/chat")
async def chat(request: Request, background_tasks: BackgroundTasks, input: ChatbotRequest):
    chatbot_app = ChatbotApplication(request=request)
    result = await chatbot_app.run(ChatbotApplicationInput(
        raw_question=input.question,
        user_id="user_id",
        conversation_id="conversation_id",
        conversation_history=[]
    ), background_tasks)
    return JSONResponse(content=result.model_dump())