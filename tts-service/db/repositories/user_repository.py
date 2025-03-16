from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.user import User


class UserRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.users

    async def get_by_id(self, id: str) -> Optional[User]:
        user = await self.collection.find_one({"_id": ObjectId(id)})
        if user:
            return User.model_validate(user)
        return None

    async def get_by_email(self, email: str) -> Optional[User]:
        user = await self.collection.find_one({"email": email})
        if user:
            return User.model_validate(user)
        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        user = await self.collection.find_one({"username": username})
        if user:
            return User.model_validate(user)
        return None

    async def create(self, user_data: Dict[str, Any]) -> User:
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = user_data["created_at"]

        if "_id" in user_data and isinstance(user_data["_id"], str):
            user_data["_id"] = ObjectId(user_data["_id"])

        result = await self.collection.insert_one(user_data)
        user = await self.collection.find_one({"_id": result.inserted_id})
        return User.model_validate(user)

    async def update(self, id: str, user_data: Dict[str, Any]) -> Optional[User]:
        user_data["updated_at"] = datetime.utcnow()

        if "_id" in user_data:
            del user_data["_id"]

        await self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": user_data}
        )
        return await self.get_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        users = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for document in cursor:
            users.append(User.model_validate(document))
        return users