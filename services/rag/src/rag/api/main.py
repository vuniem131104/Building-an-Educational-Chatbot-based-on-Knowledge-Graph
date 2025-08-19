from fastapi import Request 
from fastapi import APIRouter
from fastapi.responses import JSONResponse 
from rag.application.local_search import LocalSearchApplication, LocalSearchApplicationInput
from base import BaseModel
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1")

class LocalSearchRequest(BaseModel):
    query: str


@router.post("/local_search")
async def local_search(request: Request, local_search_request: LocalSearchRequest):
    """
    Perform a local search using the provided query.
    """
    application = LocalSearchApplication(request=request)
    result = await application.run(inputs=LocalSearchApplicationInput(input_text=local_search_request.query))
    return JSONResponse(content=result.model_dump())
