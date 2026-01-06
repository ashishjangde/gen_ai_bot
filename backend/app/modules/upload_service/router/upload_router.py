from fastapi import APIRouter , UploadFile , Form ,Depends
from app.modules.upload_service.schema.upload_schema import UploadFileResponse, UploadMeta
from app.advices.response import SuccessResponseSchema
from app.modules.upload_service.service.upload_service import get_upload_service
from app.modules.upload_service.service.upload_service import UploadService

router = APIRouter()


def upload_meta(
    file_name: str = Form(...),
    user_id: str = Form(...),
) -> UploadMeta:
    return UploadMeta(
        file_name=file_name,
        user_id=user_id,
    )


@router.post("/upload" , response_model= SuccessResponseSchema[UploadFileResponse])
async def upload_file(
    file: UploadFile,
    meta : UploadMeta = Depends(upload_meta),
    service: UploadService = Depends(get_upload_service)
):
    result = await service.upload_file(file, meta)
    return SuccessResponseSchema(data=result)
