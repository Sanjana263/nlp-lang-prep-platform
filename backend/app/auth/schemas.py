from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TargetExam = Literal["IELTS", "TOEFL", "PTE"]


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    target_exam: TargetExam

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name must not be blank")
        return v

    @field_validator("password")
    @classmethod
    def _bcrypt_limit(cls, v: str) -> str:
        # bcrypt only handles 72 *bytes* (not characters)
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: str
    target_exam: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    target_exam: Optional[TargetExam] = None
