import uuid
from fastapi import UploadFile, Depends
from typing import AsyncGenerator
from app.modules.utils.object_service import get_object_service, ObjectService
from app.modules.upload_service.schema.upload_schema import UploadMeta, UploadFileResponse

class UploadService:
    def __init__(self, object_service: ObjectService):
        self.object_service = object_service

    async def _file_iterator(self, file: UploadFile, chunk_size: int = 10 * 1024 * 1024) -> AsyncGenerator[bytes, None]:
        """Async generator to yield file chunks."""
        while chunk := await file.read(chunk_size):
            yield chunk

    async def upload_file(self, file: UploadFile, meta: UploadMeta , user_id: str) -> UploadFileResponse:
        file_id = str(uuid.uuid4())
        key = f"{user_id}/{file_id}/{meta.file_name}"
        
        await self.object_service.upload_stream(
            stream=self._file_iterator(file),
            key=key,
            content_type=file.content_type or "application/octet-stream"
        )
        
        presigned_url = self.object_service.get_url(key)
        
        return UploadFileResponse(
            file_id=file_id,
            file_name=meta.file_name,
            user_id=user_id,
            file_url=key,
            presigned_url=presigned_url
        )



async def get_upload_service(object_service: ObjectService = Depends(get_object_service)) -> UploadService:
    return UploadService(object_service)
