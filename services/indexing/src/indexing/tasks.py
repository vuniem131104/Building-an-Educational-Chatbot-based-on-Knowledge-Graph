from indexing.celery_app import celery_app
from indexing.application.indexing import IndexingApplication, IndexingApplicationInput
from indexing.shared.utils import get_settings
from lite_llm import LiteLLMService
from storage.minio import MinioService
from graph_db import Neo4jService
from logger import get_logger
import asyncio

logger = get_logger(__name__)

class MockRequest:
    """Mock request object để có thể sử dụng IndexingApplication trong Celery task"""
    def __init__(self):
        self.app = MockApp()

class MockApp:
    """Mock app object với state cần thiết"""
    def __init__(self):
        self.state = MockState()

class MockState:
    """Mock state với các services cần thiết"""
    def __init__(self):
        settings = get_settings()
        self.settings = settings
        self.litellm_service = LiteLLMService(
            litellm_setting=settings.litellm
        )
        self.minio_service = MinioService(
            settings=settings.minio
        )
        self.neo4j_service = Neo4jService(
            settings=settings.neo4j
        )

@celery_app.task(name="tasks.index_file", bind=True)
def index_file_task(self, file_name: str):
    """
    Celery task để xử lý indexing file
    Sử dụng IndexingApplication thay vì duplicate code
    """
    try:
        logger.info(
            'Starting indexing task',
            extra={
                'file_name': file_name,
                'task_id': self.request.id
            }
        )
        
        # Tạo mock request để sử dụng IndexingApplication
        mock_request = MockRequest()
        
        # Khởi tạo IndexingApplication
        indexing_app = IndexingApplication(request=mock_request)
        
        # Chạy indexing (cần wrap trong asyncio vì run() là async)
        result = asyncio.run(
            indexing_app.run(
                IndexingApplicationInput(file_name=file_name)
            )
        )
        
        logger.info(
            'Indexing task completed successfully',
            extra={
                'file_name': file_name,
                'task_id': self.request.id
            }
        )
        
        return {
            "status": "success",
            "file_name": file_name,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.exception(
            'Indexing task failed',
            extra={
                'file_name': file_name,
                'task_id': self.request.id,
                'error': str(e)
            }
        )
        
        # Retry task nếu cần
        raise self.retry(countdown=60, max_retries=3)
