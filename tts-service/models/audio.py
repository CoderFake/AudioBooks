from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from models.user import PyObjectId

class AudioSegment(BaseModel):
    start_index: int
    end_index: int
    start_time: float
    end_time: float
    text: str
    url: str

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

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "voice_model": "female",
                "url": "https://storage.googleapis.com/bucket/audio.mp3",
                "duration": 120.5,
                "format": "mp3",
                "sample_rate": 22050,
            }
        }