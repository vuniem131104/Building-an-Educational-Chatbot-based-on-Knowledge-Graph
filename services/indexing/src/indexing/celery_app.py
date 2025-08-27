from celery import Celery

from indexing.shared.utils import get_settings 

settings = get_settings()

celery_app = Celery(
    "tasks",
    broker=f"redis://{settings.redis.host}:{settings.redis.port}/{settings.redis.db}",
    backend=f"redis://{settings.redis.host}:{settings.redis.port}/{settings.redis.db}"
)

celery_app.conf.task_routes = {
    "tasks.index_file": {"queue": "indexing"},
}
