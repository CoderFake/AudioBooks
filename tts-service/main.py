import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import setup_logging
from db.mongodb import connect_to_mongo, close_mongo_connection
from api.router import api_router

# Thiết lập logging
logger = setup_logging()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Thêm middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production, nên giới hạn danh sách nguồn gốc
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Chào mừng đến với API Text-to-Speech Tiếng Việt",
        "docs": "/docs",
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )