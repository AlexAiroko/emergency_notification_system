import logging
from io import BytesIO

from minio import Minio

from app.core.config import settings


logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self):
        self._client: Minio | None = None

    def _ensure_client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )

            if not self._client.bucket_exists(settings.MINIO_BUCKET):
                self._client.make_bucket(settings.MINIO_BUCKET)
                logger.info("Created bucket: %s", settings.MINIO_BUCKET)
        return self._client

    def upload(self, object_name: str, data: bytes) -> None:
        client = self._ensure_client()
        client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            BytesIO(data),
            length=len(data),
        )
        logger.info("Uploaded %s bytes to s3://%s/%s", len(data), settings.MINIO_BUCKET, object_name)

    def download(self, object_name: str) -> bytes:
        client = self._ensure_client()
        response = client.get_object(settings.MINIO_BUCKET, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, object_name: str) -> None:
        client = self._ensure_client()
        client.remove_object(settings.MINIO_BUCKET, object_name)
        logger.info("Deleted s3://%s/%s", settings.MINIO_BUCKET, object_name)


_s3_client: S3Client | None = None


def get_s3_client() -> S3Client:
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
