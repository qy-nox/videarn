from uuid import UUID
from pydantic import BaseModel, Field
class FirebaseLoginRequest(BaseModel):
    id_token: str = Field(min_length=20)
class TokenResponse(BaseModel):
    access_token: str; refresh_token: str; token_type: str = "bearer"
class RefreshRequest(BaseModel):
    refresh_token: str
class UserResponse(BaseModel):
    id: UUID; username: str|None; email: str|None; phone_verified: bool
    model_config = {"from_attributes": True}
