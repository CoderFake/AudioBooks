from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.schema_with_serializer(
            core_schema.str_schema(),
            lambda obj: str(obj),
            serialization=core_schema.SerializationInfo(
                json_schema_extra={"type": "string"}
            ),
        )

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

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "title": "Truyện ngắn",
                "content": "Đây là nội dung văn bản cần chuyển thành âm thanh.",
                "language": "vi",
                "tags": ["truyện ngắn", "văn học"],
            }
        }
    }