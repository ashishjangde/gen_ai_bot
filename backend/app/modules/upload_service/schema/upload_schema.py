from pydantic import BaseModel , Field


class UploadMeta(BaseModel):
    file_name: str = Field(... , examples=["file_name"])
    user_id: str | None = Field(default=None , examples=["user_id"])


class UploadFileResponse(BaseModel):
    file_id: str = Field(... , examples=["file_id"])
    file_name: str = Field(... , examples=["file_name"])
    user_id: str = Field(... , examples=["user_id"])
    file_url: str = Field(... , examples=["file_url"])
    presigned_url: str = Field(... , examples=["presigned_url"])
