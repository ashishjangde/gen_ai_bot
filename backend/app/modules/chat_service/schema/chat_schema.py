from pydantic import BaseModel, root_validator
from typing import Optional




class ChatRequestSchema(BaseModel):
    session_id: str
    message: Optional[str] = None
    file_url: Optional[str] = None

    @root_validator
    def validate_request(cls, values):
        message = values.get("message")
        file_url = values.get("file_url")

        if not message and not file_url:
            raise ValueError("Either message or file_url is required")

        return values

