from typing import Optional, List, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId

def validate_object_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str):
        try:
            return str(ObjectId(v))
        except Exception:
            raise ValueError("Invalid ObjectId format")
    raise ValueError("Invalid ObjectId type")

PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]

class Text(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId
    title: str
    content: str
    language: str = "vi"
    tags: List[str] = []
    status: str = "pending"
    processing_error: Optional[str] = None
    word_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "title": "Truyện ngắn",
                "content": "Đây là nội dung văn bản cần chuyển thành âm thanh.",
                "language": "vi",
                "tags": ["truyện ngắn", "văn học"],
            }
        }
    }

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True)
        if data.get("_id"):
            data["_id"] = ObjectId(data["_id"])
        if data.get("user_id"):
            data["user_id"] = ObjectId(data["user_id"])
        return data