from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.text import Text


class TextRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.texts

    async def get_by_id(self, id: str) -> Optional[Text]:
        text = await self.collection.find_one({"_id": ObjectId(id)})
        if text:
            return Text(**text)
        return None

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Text]:
        texts = []
        cursor = self.collection.find({"user_id": ObjectId(user_id)}).skip(skip).limit(limit)
        async for document in cursor:
            texts.append(Text(**document))
        return texts

    async def create(self, text_data: dict) -> Text:
        if "user_id" in text_data and isinstance(text_data["user_id"], str):
            text_data["user_id"] = ObjectId(text_data["user_id"])

        text_data["word_count"] = len(text_data.get("content", "").split())

        text_data["created_at"] = datetime.utcnow()
        text_data["updated_at"] = text_data["created_at"]
        text_data["status"] = "pending"

        result = await self.collection.insert_one(text_data)
        text = await self.collection.find_one({"_id": result.inserted_id})
        return Text(**text)

    async def update(self, id: str, text_data: dict) -> Optional[Text]:
        if "content" in text_data:
            text_data["word_count"] = len(text_data["content"].split())

        text_data["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": text_data}
        )
        return await self.get_by_id(id)

    async def update_status(self, id: str, status: str, error: Optional[str] = None) -> Optional[Text]:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if error:
            update_data["processing_error"] = error

        await self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )
        return await self.get_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Text]:
        texts = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for document in cursor:
            texts.append(Text(**document))
        return texts