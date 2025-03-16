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
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    text_id: PyObjectId
    user_id: PyObjectId
    voice_model: str
    url: str
    duration: float
    format: str = "mp3"
    sample_rate: int = 22050
    segments: List[AudioSegment]
    status: str = "completed"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
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