import logging
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DATABASE]
    logger.info("Connected to MongoDB!")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
    logger.info("MongoDB connection closed!")

def get_database():
    return db.db