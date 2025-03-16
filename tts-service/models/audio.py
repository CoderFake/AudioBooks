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

class AudioSegment(BaseModel):
    start_index: int
    end_index: int
    start_time: float
    end_time: float
    text: str
    url: str

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class Audio(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    text_id: PyObjectId
    user_id: PyObjectId
    voice_model: str
    url: str
    duration: float
    format: str = "mp3"
    sample_rate: int = 22050
    segments: List[AudioSegment] = []
    status: str = "completed"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "voice_model": "female",
                "url": "https://storage.googleapis.com/bucket/audio.mp3",
                "duration": 120.5,
                "format": "mp3",
                "sample_rate": 22050,
            }
        }
    }

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True)
        if data.get("_id"):
            data["_id"] = ObjectId(data["_id"])
        if data.get("text_id"):
            data["text_id"] = ObjectId(data["text_id"])
        if data.get("user_id"):
            data["user_id"] = ObjectId(data["user_id"])
        return data