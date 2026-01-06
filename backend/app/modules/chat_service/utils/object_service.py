import asyncio
import logging
from typing import Optional, AsyncIterator, List
from functools import lru_cache
import httpx
from boto3 import client
from botocore.exceptions import ClientError

from app.config.settings import settings

logger = logging.getLogger(__name__)

@lru_cache
def _get_s3_client():
    return client(
        "s3",
        region_name=settings.supabase_region,
        endpoint_url=settings.supabase_endpoint,
        aws_access_key_id=settings.supabase_access_key_id,
        aws_secret_access_key=settings.supabase_access_key_secret,
    )


class ObjectService:
    """
    Async S3-compatible object storage.

    - boto3 (sync) → presigned URLs + metadata ops
    - httpx (async) → upload/download
    """

    def __init__(self, bucket: str = "documents"):
        self.bucket = bucket
        self._s3 = _get_s3_client()
        self._http: Optional[httpx.AsyncClient] = None

    async def connect(self):
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(None))
            logger.info("ObjectService connected")

    async def close(self):
        if self._http:
            await self._http.aclose()
            self._http = None
            logger.info("ObjectService closed")

    def _ensure_connected(self):
        if self._http is None:
            raise RuntimeError("ObjectService not connected")

    def _presigned_put(
        self,
        key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        return self._s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    def _presigned_get(self, key: str, expires_in: int = 3600) -> str:
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        self._ensure_connected()
        try:
            url = self._presigned_put(key, content_type)
            resp = await self._http.put(
                url,
                content=data,
                headers={"Content-Type": content_type},
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.exception(f"Upload failed: {key}")
            return False

    async def upload_stream(
        self,
        stream: AsyncIterator[bytes],
        key: str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """
        Use this for large files (Parquet, video, blobs).
        """
        self._ensure_connected()
        try:
            url = self._presigned_put(key, content_type)
            resp = await self._http.put(
                url,
                content=stream,
                headers={"Content-Type": content_type},
            )
            resp.raise_for_status()
            return True
        except Exception:
            logger.exception(f"Streaming upload failed: {key}")
            return False

    async def get_bytes(self, key: str) -> Optional[bytes]:
        self._ensure_connected()
        try:
            url = self._presigned_get(key)
            resp = await self._http.get(url)
            resp.raise_for_status()
            return resp.content
        except Exception:
            logger.exception(f"Get failed: {key}")
            return None

    async def stream(self, key: str) -> AsyncIterator[bytes]:
        """
        Stream large objects without loading into memory.
        """
        self._ensure_connected()
        url = self._presigned_get(key)
        async with self._http.stream("GET", url) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                yield chunk


    async def delete(self, key: str) -> bool:
        try:
            await asyncio.to_thread(
                self._s3.delete_object,
                Bucket=self.bucket,
                key=key
            )
            return True
        except Exception:
            logger.exception(f"Delete failed: {key}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(
                self._s3.head_object,
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError:
            return False

    async def list(self, prefix: str = "") -> List[str]:
        """
        Paginated list (safe for large buckets).
        """
        keys: List[str] = []
        continuation: Optional[str] = None

        try:
            while True:
                response = await asyncio.to_thread(
                    self._s3.list_objects_v2,
                    Bucket=self.bucket,
                    Prefix=prefix,
                    ContinuationToken=continuation,
                )

                for obj in response.get("Contents", []):
                    keys.append(obj["Key"])

                if not response.get("IsTruncated"):
                    break

                continuation = response.get("NextContinuationToken")

            return keys
        except Exception:
            logger.exception("List failed")
            return []

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        return self._presigned_get(key, expires_in)
