from fastapi import APIRouter , UploadFile , Form ,Depends
from app.modules.upload_service.schema.upload_schema import UploadFileResponse, UploadMeta
from app.advices.response import SuccessResponseSchema
from app.modules.upload_service.service.upload_service import get_upload_service
from app.modules.upload_service.service.upload_service import UploadService
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


def upload_meta(
    file_name: str = Form(...),
) -> UploadMeta:
    return UploadMeta(
        file_name=file_name
    )


@router.post("" , response_model= SuccessResponseSchema[UploadFileResponse])
async def upload_file(
    file: UploadFile,
    meta : UploadMeta = Depends(upload_meta),
    user : CurrentUser = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service)
):
    user_id = str(user.id)
    result = await service.upload_file(file, meta , user_id)
    return SuccessResponseSchema(data=result)
