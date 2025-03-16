import os
from typing import ClassVar
from pydantic import field_validator, BaseModel
from dotenv import load_dotenv

# Tải file .env trước
load_dotenv('/app/.env')

class Settings(BaseModel):
    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "TTS Service")

    # MongoDB Settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "audiobooksDB")

    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b95c1b8ada2d169d69c18f6323cfc2ff9d103329b2ae53a4a2922a17e4bde385")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Firebase Settings
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "dev-project-id")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "dummy-private-key")
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "dummy@example.com")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "dev-bucket")

    DEFAULT_VOICE_MODEL: str = os.getenv("DEFAULT_VOICE_MODEL", "female")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "5000"))
    TTS_TEMP_DIR: str = os.getenv("TTS_TEMP_DIR", "/tmp/tts_temp")

    model_config: ClassVar[dict] = {
        "populate_by_name": True
    }

    @field_validator("TTS_TEMP_DIR")
    @classmethod
    def create_tts_temp_dir(cls, v):
        os.makedirs(v, exist_ok=True)
        return v

    @field_validator("FIREBASE_PRIVATE_KEY")
    @classmethod
    def decode_firebase_key(cls, v):
        return v.replace("\\n", "\n")


settings = Settings()