from typing import Optional, List
from pydantic import BaseModel

class AudioSegmentBase(BaseModel):
    start_index: int
    end_index: int
    start_time: float
    end_time: float
    text: str
    url: Optional[str] = None

class AudioBase(BaseModel):
    text_id: str
    voice_model: str = "female"
    format: str = "mp3"
    sample_rate: int = 22050

class AudioCreate(AudioBase):
    pass

class AudioSegmentResponse(AudioSegmentBase):
    pass

class AudioResponse(AudioBase):
    id: str
    user_id: str
    url: str
    duration: float
    segments: List[AudioSegmentResponse] = []
    status: str
    error: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "60d9b4b9f5b5f5b5f5b5f5b5",
                "text_id": "60d9b4b9f5b5f5b5f5b5f5b5",
                "user_id": "60d9b4b9f5b5f5b5f5b5f5b5",
                "voice_model": "female",
                "url": "https://storage.googleapis.com/bucket/audio.mp3",
                "duration": 120.5,
                "format": "mp3",
                "sample_rate": 22050,
                "segments": [
                    {
                        "start_index": 0,
                        "end_index": 100,
                        "start_time": 0.0,
                        "end_time": 10.5,
                        "text": "Đoạn văn bản đầu tiên",
                        "url": "https://storage.googleapis.com/bucket/segment_1.mp3"
                    }
                ],
                "status": "completed",
                "created_at": "2023-07-15T10:35:00",
                "updated_at": "2023-07-15T10:40:00"
            }
        }
    }

class TTSRequest(BaseModel):
    text_id: str
    voice_model: str = "female"
    format: str = "mp3"
    sample_rate: int = 22050
    split_into_segments: bool = True