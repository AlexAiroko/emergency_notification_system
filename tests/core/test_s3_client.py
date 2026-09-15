from unittest.mock import Mock, patch

from app.core.s3 import S3Client, get_s3_client


class FakeS3Response:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def close(self):
        pass

    def release_conn(self):
        pass


def test_upload():
    with patch("app.core.s3.Minio") as mock_minio_cls:
        mock_client = Mock()
        mock_client.bucket_exists.return_value = True
        mock_minio_cls.return_value = mock_client

        s3 = S3Client()
        s3.upload("imports/1/file.csv", b"content")

        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args.args[0] == "ens-imports"
        assert call_args.args[1] == "imports/1/file.csv"


def test_download():
    with patch("app.core.s3.Minio") as mock_minio_cls:
        mock_client = Mock()
        mock_client.bucket_exists.return_value = True
        mock_response = FakeS3Response(b"file content")
        mock_client.get_object.return_value = mock_response
        mock_minio_cls.return_value = mock_client

        s3 = S3Client()
        result = s3.download("imports/1/file.csv")

        assert result == b"file content"
        mock_client.get_object.assert_called_once_with("ens-imports", "imports/1/file.csv")


def test_delete():
    with patch("app.core.s3.Minio") as mock_minio_cls:
        mock_client = Mock()
        mock_client.bucket_exists.return_value = True
        mock_minio_cls.return_value = mock_client

        s3 = S3Client()
        s3.delete("imports/1/file.csv")

        mock_client.remove_object.assert_called_once_with("ens-imports", "imports/1/file.csv")


def test_singleton():
    with patch("app.core.s3.Minio") as mock_minio_cls:
        mock_client = Mock()
        mock_client.bucket_exists.return_value = True
        mock_minio_cls.return_value = mock_client

        import app.core.s3 as s3_module
        original = s3_module._s3_client
        s3_module._s3_client = None

        try:
            client1 = get_s3_client()
            client2 = get_s3_client()
            assert client1 is client2
        finally:
            s3_module._s3_client = original
