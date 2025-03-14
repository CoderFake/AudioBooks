import os
try:
    from pydantic_settings import BaseSettings
    from pydantic import validator
except ImportError:
    from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    PROJECT_NAME: str = "TTS Service"

    # MongoDB Settings
    MONGODB_URL: str
    MONGODB_DATABASE: str

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Firebase Settings
    FIREBASE_PROJECT_ID: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_STORAGE_BUCKET: str

    DEFAULT_VOICE_MODEL: str = "female"
    CHUNK_SIZE: int = 5000
    TTS_TEMP_DIR: str = "/tmp/tts_temp"

    @validator("TTS_TEMP_DIR")
    def create_tts_temp_dir(cls, v):
        os.makedirs(v, exist_ok=True)
        return v

    @validator("FIREBASE_PRIVATE_KEY")
    def decode_firebase_key(cls, v):
        return v.replace("\\n", "\n")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()