import re
from pydantic import BaseModel, Field, field_validator, ConfigDict


class UpdateUserSchema(BaseModel):
    """Schema for updating user profile"""
    name: str | None = Field(None, min_length=3, max_length=50)


class ChangePasswordSchema(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., min_length=8, max_length=50)
    new_password: str = Field(..., min_length=8, max_length=50)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", v):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")
        return v
