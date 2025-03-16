from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: str
    disabled: bool = False
    is_admin: bool = False

class UserResponse(UserBase):
    id: str
    disabled: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "60d9b4b9f5b5f5b5f5b5f5b5",
                "email": "user@example.com",
                "username": "username",
                "full_name": "Nguyen Van A",
                "disabled": False
            }
        }
    }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None