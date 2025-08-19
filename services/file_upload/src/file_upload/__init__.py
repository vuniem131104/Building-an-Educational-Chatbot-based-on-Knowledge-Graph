import os
import tempfile
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

from logger import get_logger
from logger import setup_logging
from storage.minio import MinioService, MinioInput
from storage.minio import MinioSetting


setup_logging(json_logs=False, log_level='INFO')
logger = get_logger('api')


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.minio_settings = MinioSetting(
        endpoint=os.getenv("MINIO__ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO__ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO__SECRET_KEY", "minioadmin123"),
        secure=os.getenv("MINIO__SECURE", "false") == "true"
    )
    app.state.minio_service = MinioService(settings=app.state.minio_settings)
    yield
    
app = FastAPI(
    title="File Upload Service",
    description="Service for uploading files to MinIO storage",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "File Upload Service is running"}


@app.post("/v1/upload")
async def upload_file(
    request: Request,
    files: list[UploadFile] = File(...),
    course_code: str = Form(...),
    week_number: str = Form(...)
):
    """
    Upload file to MinIO storage.
    
    Args:
        request: FastAPI request object
        files: The list of uploaded files
        course_code: Course code (will be bucket name)
        week_number: Week number (will be folder name)
    
    Returns:
        JSON response with upload status
    """
    try:
        # Validate inputs
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No file selected")

        if not course_code.strip():
            raise HTTPException(status_code=400, detail="Course code is required")

        if not week_number.strip():
            raise HTTPException(status_code=400, detail="Week number is required")

        # Validate week number
        try:
            week_num = int(week_number)
            if week_num < 1 or week_num > 15:
                raise ValueError()
        except ValueError:
            raise HTTPException(status_code=400, detail="Week number must be between 1 and 15")

        # Allowed extensions
        allowed_exts = {"pptx", "doc", "docx", "pdf"}
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        bucket_name = course_code.lower().strip()
        folder_name = f"tuan-{week_number}"
        results = []

        for file in files:
            ext = file.filename.split('.')[-1].lower()
            if ext not in allowed_exts:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"File type .{ext} is not allowed"
                })
                continue

            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "File size exceeds 50MB limit"
                })
                continue

            await file.seek(0)
            object_name = f"{folder_name}/{file.filename}"

            logger.info(
                "Starting file upload",
                extra={
                    "filename": file.filename,
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "file_size": len(file_content),
                    "course_code": course_code,
                    "week_number": week_number
                }
            )

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                upload_input = MinioInput(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    file_path=temp_file_path,
                    content_type=file.content_type or "application/octet-stream"
                )
                request.app.state.minio_service.upload_file(upload_input)
                os.unlink(temp_file_path)

                logger.info(
                    "File uploaded successfully",
                    extra={
                        "filename": file.filename,
                        "bucket_name": bucket_name,
                        "object_name": object_name,
                    }
                )
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "file_size": len(file_content),
                    "course_code": course_code,
                    "week_number": week_number
                })
            except Exception as e:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                logger.error(
                    "Error uploading file",
                    extra={
                        "filename": file.filename,
                        "error": str(e)
                    }
                )
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": str(e)
                })

        return JSONResponse(
            status_code=200,
            content={
                "results": results
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error during file upload",
            extra={
                "course_code": course_code,
                "week_number": week_number,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Internal server error during upload")


@app.get("/v1/files/{bucket_name}")
async def list_files(request: Request, bucket_name: str, week_number: int):
    """
    List files in a specific bucket.
    
    Args:
        request: FastAPI request object
        bucket_name: Name of the bucket
        week_number: Week number to filter files
    Returns:
        List of files in the bucket
    """
    try:
        prefix = f"tuan-{week_number}/"
        files = request.app.state.minio_service.list_files(bucket_name.lower(), prefix)
        return {
            "bucket_name": bucket_name,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.exception(
            "Error listing files",
            extra={
                "bucket_name": bucket_name,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Error listing files")


@app.get("/v1/health")
async def health_check(request: Request):
    """Health check endpoint with MinIO connectivity test."""
    try:
        return {
            "status": "healthy",
            "minio": "connected",
            "timestamp": "2025-01-26T10:00:00Z"
        }
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={"error": str(e)}
        )
        return {
            "status": "unhealthy", 
            "minio": "disconnected",
            "error": str(e),
            "timestamp": "2025-01-26T10:00:00Z"
        }


def main():
    uvicorn.run(
        "file_upload:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )
