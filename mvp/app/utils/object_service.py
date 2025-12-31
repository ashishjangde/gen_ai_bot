import logging
from typing import Optional
import httpx
from boto3 import client
from functools import lru_cache
from mvp.app.config.settings import settings

logger = logging.getLogger(__name__)


@lru_cache()
def _get_s3_client():
    """Sync boto3 client for generating presigned URLs only."""
    return client(
        "s3",
        region_name=settings.supabase_region,
        endpoint_url=settings.supabase_endpoint,
        aws_access_key_id=settings.supabase_access_key_id,
        aws_secret_access_key=settings.supabase_access_key_secret,
    )


class ObjectService:
    """
    Async S3 storage using httpx + presigned URLs.
    - boto3 (sync) → generates presigned URLs
    - httpx (async) → actual upload/download
    """
    
    def __init__(self, bucket: str):
        self.bucket = bucket
        self._s3 = _get_s3_client()
        self._http: Optional[httpx.AsyncClient] = None
    
    async def connect(self):
        """Create async HTTP client. Call at app startup."""
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=None) 
            logger.info("ObjectService connected")
    
    async def close(self):
        """Close HTTP client. Call at app shutdown."""
        if self._http:
            await self._http.aclose()
            self._http = None
            logger.info("ObjectService closed")
    
    def _ensure_connected(self):
        if self._http is None:
            raise RuntimeError("ObjectService not connected. Call await service.connect() first.")
    
    def _presigned_put(self, key: str, content_type: str = "application/octet-stream", expires_in: int = 3600) -> str:
        """Generate presigned PUT URL."""
        return self._s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in
        )
    
    def _presigned_get(self, key: str, expires_in: int = 3600) -> str:
        """Generate presigned GET URL."""
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in
        )
    
    async def upload(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> bool:
        """Upload bytes to S3."""
        self._ensure_connected()
        try:
            url = self._presigned_put(key, content_type)
            response = await self._http.put(url, content=data, headers={"Content-Type": content_type})
            response.raise_for_status()
            logger.info(f"Uploaded → {key}")
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    async def get(self, key: str) -> Optional[bytes]:
        """Get object content as bytes."""
        self._ensure_connected()
        try:
            url = self._presigned_get(key)
            response = await self._http.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Get failed: {e}")
            return None
    

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned download URL (sync, instant)."""
        return self._presigned_get(key, expires_in)
    
    async def delete(self, key: str) -> bool:
        """Delete an object."""
        try:
            self._s3.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted {key}")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if object exists."""
        try:
            self._s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
    
    async def list(self, prefix: str = "") -> list[str]:
        """List objects by prefix."""
        try:
            response = self._s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except Exception as e:
            logger.error(f"List failed: {e}")
            return []


