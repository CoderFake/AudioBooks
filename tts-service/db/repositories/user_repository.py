from datetime import datetime
from typing import List, Optional
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
            return User(**user)
        return None

    async def get_by_email(self, email: str) -> Optional[User]:
        user = await self.collection.find_one({"email": email})
        if user:
            return User(**user)
        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        user = await self.collection.find_one({"username": username})
        if user:
            return User(**user)
        return None

    async def create(self, user_data: dict) -> User:
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = user_data["created_at"]
        result = await self.collection.insert_one(user_data)
        user = await self.collection.find_one({"_id": result.inserted_id})
        return User(**user)

    async def update(self, id: str, user_data: dict) -> Optional[User]:
        user_data["updated_at"] = datetime.utcnow()
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
            users.append(User(**document))
        return users