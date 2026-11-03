from datetime import timedelta
from uuid import UUID
import boto3
from botocore.client import Config
from app.core.config import get_settings

class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        kwargs = {"region_name": settings.s3_region}
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        if settings.s3_access_key_id and settings.s3_secret_access_key:
            kwargs["aws_access_key_id"] = settings.s3_access_key_id
            kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
        self.client = boto3.client("s3", config=Config(signature_version="s3v4"), **kwargs)
        self.bucket = settings.s3_bucket
        self.cdn_base_url = settings.cdn_base_url

    def presigned_upload(self, key: str, content_type: str, expires: int = 900) -> str:
        return self.client.generate_presigned_url(
            "put_object", Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
        )

    def public_url(self, key: str) -> str:
        if self.cdn_base_url:
            return f"{self.cdn_base_url.rstrip('/')}/{key}"
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=3600
        )

    def download(self, key: str, destination: str) -> None:
        self.client.download_file(self.bucket, key, destination)

    def upload_file(self, path: str, key: str, content_type: str) -> None:
        self.client.upload_file(path, self.bucket, key, ExtraArgs={"ContentType": content_type})

storage = StorageService
