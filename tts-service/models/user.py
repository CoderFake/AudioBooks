from typing import Optional, Any, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class PyObjectId(ObjectId):
    # Phiên bản đơn giản nhất cho Pydantic v2
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    def __str__(self):
        return str(self)

    def __repr__(self):
        return f"PyObjectId({super().__repr__()})"


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: str
    disabled: bool = False
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "username": "user",
                "email": "user@example.com",
                "full_name": "User",
                "disabled": False,
                "is_admin": False
            }
        }
    }