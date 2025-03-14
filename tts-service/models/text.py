from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from models.user import PyObjectId

class Text(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    title: str
    content: str
    language: str = "vi"
    tags: List[str]
    status: str = "pending"
    processing_error: Optional[str] = None
    word_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "Truyện ngắn",
                "content": "Đây là nội dung văn bản cần chuyển thành âm thanh.",
                "language": "vi",
                "tags": ["truyện ngắn", "văn học"],
            }
        }