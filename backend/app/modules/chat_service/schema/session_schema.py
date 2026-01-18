from pydantic import BaseModel


class InitializeSessionResponseSchema(BaseModel):
    session_id: str
    prompt: str