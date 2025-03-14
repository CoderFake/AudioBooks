from fastapi import APIRouter

from api.endpoints import auth, texts, audio

# Khởi tạo router chính
api_router = APIRouter()

# Bao gồm các router con
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(texts.router, prefix="/texts", tags=["texts"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])