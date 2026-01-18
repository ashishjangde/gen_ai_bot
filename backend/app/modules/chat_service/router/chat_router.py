from app.modules.chat_service.schema.chat_schema import ChatRequestSchema
from fastapi import APIRouter,Depends
from app.middlewares.dependencies import get_current_user , CurrentUser
from app.modules.chat_service.service.chat_service import get_chat_service, ChatService
from app.advices.response import SuccessResponseSchema
router = APIRouter()



@router.post("/chat")
async def chat(
    data : ChatRequestSchema,
    user : CurrentUser = Depends(get_current_user)
    chat_service : ChatService = Depends(get_chat_service)
):
    data = await chat_service.chat(user_id = user.id ,data=data)
    return SuccessResponseSchema(data=data)
    