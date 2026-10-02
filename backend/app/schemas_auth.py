"""Request and response shapes for login."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=72)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in_minutes: int


class UserOut(BaseModel):
    user_id: int
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool