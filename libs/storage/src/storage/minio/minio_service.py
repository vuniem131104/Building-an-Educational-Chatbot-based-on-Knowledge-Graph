from __future__ import annotations

from io import BytesIO
from typing import Optional

from minio import Minio  # type:ignore
from minio.error import S3Error  # type:ignore
from .settings import MinioSetting

from ..base import StorageBase
from ..base import StorageBaseInput
from ..base import StorageBaseOutput


class MinioInput(StorageBaseInput):
    file_path: Optional[str] = None
    data: Optional[BytesIO] = None
    content_type: Optional[str] = None
    metadata: Optional[dict] = None


class MinioOutput(StorageBaseOutput):
    pass

class MinioService(StorageBase):
    settings: MinioSetting

    @property
    def _client(self) -> Minio:
        return Minio(
            endpoint=self.settings.endpoint,
            access_key=self.settings.access_key,
            secret_key=self.settings.secret_key,
            secure=self.settings.secure,
        )

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists in MinIO.

        Args:
            bucket_name (str): The name of the bucket to check.

        Returns:
            bool: True if the bucket exists, False otherwise.
        """
        is_exist = self._client.bucket_exists(bucket_name)
        return is_exist

    def create_bucket(self, bucket_name: str) -> None:
        """Create a new bucket in MinIO.

        Args:
            bucket_name (str): The name of the bucket to create.
        Raises:
            ValueError: If the bucket already exists.
        """
        if not self.bucket_exists(bucket_name):
            self._client.make_bucket(bucket_name)
        else:
            raise ValueError(f"Bucket '{bucket_name}' already exists and cannot be created again.")

    def delete_bucket(self, bucket_name: str) -> None:
        """Delete a bucket in MinIO.

        Args:
            bucket_name (str): The name of the bucket to delete.
        Raises:
            ValueError: If the bucket does not exist.
        """
        if self.bucket_exists(bucket_name):
            objects = self._client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                self._client.remove_object(bucket_name, obj.object_name)
            self._client.remove_bucket(bucket_name)
        else:
            raise ValueError(f"Bucket '{bucket_name}' does not exist and cannot be deleted.")

    def upload_file(self, input: MinioInput) -> MinioOutput:
        """Upload a file to MinIO.

        Args:
            input (MinioInput): The input data for the upload.

        Returns:
            MinioOutput: The output data after the upload.
        Raises:
            ValueError: If the bucket does not exist.
        """
        if not self.bucket_exists(input.bucket_name):
            raise ValueError(f"Bucket '{input.bucket_name}' does not exist.")

        self._client.fput_object(
            bucket_name=input.bucket_name,
            object_name=input.object_name,
            file_path=input.file_path,
            content_type=input.content_type,
            metadata=input.metadata if input.metadata else None,
        )

        return MinioOutput()

    def download_file(self, input: MinioInput) -> MinioOutput:
        """Download a file from MinIO.

        Args:
            input (MinioInput): The input data for the download.

        Raises:
            ValueError: If the bucket does not exist.

        Returns:
            MinioOutput: The output data after the download.
        """
        if not self.bucket_exists(input.bucket_name):
            raise ValueError(f"Bucket '{input.bucket_name}' does not exist.")

        self._client.fget_object(
            bucket_name=input.bucket_name,
            object_name=input.object_name,
            file_path=input.file_path,
        )
        return MinioOutput()

    def delete_file(self, input: MinioInput) -> MinioOutput:
        """Delete a file from MinIO.

        Args:
            input (MinioInput): The input data for the delete.

        Returns:
            MinioOutput: The output data after the delete.
        Raises:
            ValueError: If the bucket does not exist.
        """
        if not self.bucket_exists(input.bucket_name):
            raise ValueError(f"Bucket '{input.bucket_name}' does not exist.")

        self._client.remove_object(
            bucket_name=input.bucket_name,
            object_name=input.object_name,
        )
        return MinioOutput()

    def upload_data(self, input: MinioInput) -> MinioOutput:
        """Upload data to MinIO.

        Args:
            input (MinioInput): The input data for the upload.

        Returns:
            MinioOutput: The output data after the upload.
        Raises:
            ValueError: If the bucket does not exist.
        """
        if not self.bucket_exists(input.bucket_name):
            raise ValueError(f"Bucket '{input.bucket_name}' does not exist.")

        self._client.put_object(
            bucket_name=input.bucket_name,
            object_name=input.object_name,
            data=input.data,
            length=input.data.getbuffer().nbytes if input.data else 0,
            content_type=input.content_type,
            metadata=input.metadata if input.metadata else None,
        )
        return MinioOutput()
    
    def list_files(self, bucket_name: str, prefix: str, recursive: bool = False) -> list[str]:
        """List files in a MinIO bucket.

        Args:
            bucket_name (str): The name of the bucket to list files from.
            prefix (str): The prefix to filter files by.
            recursive (bool): Whether to list files recursively.

        Returns:
            list[str]: A list of file names in the bucket.
        """
        if self.bucket_exists(bucket_name):
            objects = self._client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
            return [obj.object_name for obj in objects]
        else:
            raise ValueError(f"Bucket '{bucket_name}' does not exist.")

    def check_object_exists(self, input: MinioInput) -> bool:
        """Check if an object exists in MinIO.

        Args:
            input (MinioInput): The input data for the check.

        Returns:
            bool: True if the object exists, False otherwise.
        """
        if not self.bucket_exists(input.bucket_name):
            raise ValueError(f"Bucket '{input.bucket_name}' does not exist.")
        
        try:
            self._client.stat_object(
                bucket_name=input.bucket_name,
                object_name=input.object_name,
            )
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise
        
    def get_data_from_file(self, input: MinioInput) -> str:
        """Get data from a file in MinIO.

        Args:
            input (MinioInput): The input data for the get operation.

        Returns:
            str: The content of the object as a string.
        Raises:
            ValueError: If the bucket does not exist or the object does not exist.
        """
        if not self.bucket_exists(input.bucket_name):
            raise ValueError(f"Bucket '{input.bucket_name}' does not exist.")
        
        response = self._client.get_object(
            bucket_name=input.bucket_name,
            object_name=input.object_name,
        )
        
        data = response.read().decode("utf-8") 
        
        response.close()
        response.release_conn()
        
        return data
