from app.modules.chat_service.schema.chat_schema import ChatRequestSchema

class ChatService:
    def __init__(self):
        pass
    
    async def chat(self, user_id: str, data: ChatRequestSchema):
        pass

def get_chat_service():
    chat_service = ChatService()
    return chat_service