from fastapi import Request 
from fastapi import APIRouter
from fastapi.responses import JSONResponse 
from indexing.application.indexing import IndexingApplication, IndexingApplicationInput
from base import BaseModel
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1")

class IndexingRequest(BaseModel):
    course_code: str
    week_number: int

@router.post("/indexing")
async def indexing_sync(request: Request, indexing_request: IndexingRequest):
    indexing_app = IndexingApplication(request=request)
    result = await indexing_app.run(IndexingApplicationInput(
        course_code=indexing_request.course_code,
        week_number=indexing_request.week_number
    ))
    return JSONResponse(content={
        'status': 'Indexing completed',
        'course_code': indexing_request.course_code,
        'week_number': indexing_request.week_number
    })
