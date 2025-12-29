from app.exceptions.exceptions import ConflictException
import re
from uuid import UUID
from pydantic import ConfigDict
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime

class RegisterSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=50 , examples=["John Doe"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    password: str = Field(..., min_length=8, max_length=50, examples=["12345678@Abc"])

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", v):
            raise ConflictException("Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")
        return v



class ReturnUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id : UUID
    name : str
    email : EmailStr
    is_verified : bool
    created_at : datetime
    updated_at : datetime

class LoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=50)


class VerifySchema(BaseModel):
    email: EmailStr = Field(...)
    verification_code: str = Field(..., min_length=6, max_length=6)

class ResetPasswordSchema(BaseModel):
    email: EmailStr = Field(...)
    verification_code: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=8, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", v):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")
        return v

class ForgotPasswordSchema(BaseModel):
    email: EmailStr = Field(...)

class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    user: ReturnUserSchema

class RefreshTokenResponseSchema(BaseModel):
    access_token: str
    user: ReturnUserSchema


