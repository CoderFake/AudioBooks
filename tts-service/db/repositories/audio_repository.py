from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.audio import Audio

class AudioRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.audios

    async def get_by_id(self, id: str) -> Optional[Audio]:
        audio = await self.collection.find_one({"_id": ObjectId(id)})
        if audio:
            return Audio.model_validate(audio)
        return None

    async def get_by_text_id(self, text_id: str) -> Optional[Audio]:
        audio = await self.collection.find_one({"text_id": ObjectId(text_id)})
        if audio:
            return Audio.model_validate(audio)
        return None

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Audio]:
        audios = []
        cursor = self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).skip(skip).limit(limit)
        async for document in cursor:
            audios.append(Audio.model_validate(document))
        return audios

    async def create(self, audio_data: Dict[str, Any]) -> Audio:
        if "text_id" in audio_data and isinstance(audio_data["text_id"], str):
            audio_data["text_id"] = ObjectId(audio_data["text_id"])
        if "user_id" in audio_data and isinstance(audio_data["user_id"], str):
            audio_data["user_id"] = ObjectId(audio_data["user_id"])

        audio_data["created_at"] = datetime.utcnow()
        audio_data["updated_at"] = audio_data["created_at"]

        if "segments" not in audio_data:
            audio_data["segments"] = []

        result = await self.collection.insert_one(audio_data)
        audio = await self.collection.find_one({"_id": result.inserted_id})
        return Audio.model_validate(audio)

    async def update_status(self, id: str, status: str, error: str = None) -> Optional[Audio]:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if error:
            update_data["error"] = error

        await self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )

        return await self.get_by_id(id)

    async def update_with_segments(self, id: str, url: str, duration: float, segments: List[Dict[str, Any]]) -> Optional[Audio]:
        update_data = {
            "url": url,
            "duration": duration,
            "segments": segments,
            "status": "completed",
            "updated_at": datetime.utcnow()
        }

        await self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )

        return await self.get_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Audio]:
        audios = []
        cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
        async for document in cursor:
            audios.append(Audio.model_validate(document))
        return audios