from typing import Optional, List
from pydantic import BaseModel, Field

class TextBase(BaseModel):
    title: str
    content: str
    language: str = "vi"
    tags: List[str]

class TextCreate(TextBase):
    pass

class TextUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = None

class TextResponse(TextBase):
    id: str
    user_id: str
    status: str
    word_count: int
    processing_error: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "60d9b4b9f5b5f5b5f5b5f5b5",
                "user_id": "60d9b4b9f5b5f5b5f5b5f5b5",
                "title": "Truyện ngắn",
                "content": "Đây là nội dung văn bản cần chuyển thành âm thanh.",
                "language": "vi",
                "tags": ["truyện ngắn", "văn học"],
                "status": "completed",
                "word_count": 150,
                "created_at": "2023-07-15T10:30:00",
                "updated_at": "2023-07-15T10:35:00"
            }
        }
    }