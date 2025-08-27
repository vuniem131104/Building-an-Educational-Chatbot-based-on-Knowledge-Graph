from fastapi import Request 
from fastapi import APIRouter
from fastapi.responses import JSONResponse 
from indexing.application.indexing import IndexingApplication, IndexingApplicationInput
from base import BaseModel
from logger import get_logger
from indexing.celery_app import celery_app  

logger = get_logger(__name__)
router = APIRouter(prefix="/v1")

class IndexingRequest(BaseModel):
    file_name: str


@router.post("/indexing")
async def indexing(request: Request, indexing_request: IndexingRequest):
    """
    Index a file asynchronously using Celery queue
    """
    # Gửi task vào Celery queue - gọi trực tiếp từ Application
    task = IndexingApplication.index_file_async.delay(indexing_request.file_name)
    
    return JSONResponse(content={
        'status': 'Indexing task queued',
        'task_id': task.id,
        'file_name': indexing_request.file_name
    })

@router.get("/indexing/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Kiểm tra status của Celery task
    """
    task_result = celery_app.AsyncResult(task_id)
    
    return JSONResponse(content={
        'task_id': task_id,
        'status': task_result.status,
        'result': task_result.result if task_result.ready() else None
    })

@router.post("/indexing/sync")
async def indexing_sync(request: Request, indexing_request: IndexingRequest):
    """
    Index a file synchronously (for testing purposes)
    """
    indexing_app = IndexingApplication(request=request)
    result = await indexing_app.run(IndexingApplicationInput(file_name=indexing_request.file_name))
    return JSONResponse(content={
        'status': 'Indexing completed',
        'file_name': indexing_request.file_name
    })
