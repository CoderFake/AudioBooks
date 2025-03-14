from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from bson import ObjectId

from db.repositories.text_repository import TextRepository
from models.text import Text
from models.user import User
from schemas.text import TextCreate, TextUpdate
from utils.text_processor import preprocess_text, split_text_into_chunks


class TextService:
    def __init__(self, text_repository: TextRepository):
        self.text_repository = text_repository

    async def create_text(self, text_data: TextCreate, user: User) -> Text:
        """Tạo một văn bản mới"""
        # Tiền xử lý văn bản
        processed_content = preprocess_text(text_data.content)

        text_dict = text_data.dict()
        text_dict["content"] = processed_content
        text_dict["user_id"] = ObjectId(str(user.id))

        return await self.text_repository.create(text_dict)

    async def get_text(self, text_id: str, user: User) -> Text:
        """Lấy thông tin văn bản theo ID"""
        text = await self.text_repository.get_by_id(text_id)

        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )

        # Kiểm tra quyền truy cập (chỉ người tạo hoặc admin mới có quyền)
        if str(text.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return text

    async def update_text(self, text_id: str, text_data: TextUpdate, user: User) -> Text:
        """Cập nhật thông tin văn bản"""
        text = await self.text_repository.get_by_id(text_id)

        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )

        if str(text.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        update_dict = text_data.dict(exclude_unset=True)
        if "content" in update_dict:
            update_dict["content"] = preprocess_text(update_dict["content"])

        return await self.text_repository.update(text_id, update_dict)

    async def delete_text(self, text_id: str, user: User) -> bool:
        """Xóa văn bản"""
        text = await self.text_repository.get_by_id(text_id)

        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )

        if str(text.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return await self.text_repository.delete(text_id)

    async def get_user_texts(self, user: User, skip: int = 0, limit: int = 100) -> List[Text]:
        """Lấy danh sách văn bản của người dùng"""
        return await self.text_repository.get_by_user_id(str(user.id), skip, limit)

    async def get_all_texts(self, skip: int = 0, limit: int = 100) -> List[Text]:
        """Lấy tất cả văn bản (chỉ dành cho admin)"""
        return await self.text_repository.get_all(skip, limit)

    async def split_text_into_chunks(self, text_id: str, user: User, chunk_size: Optional[int] = None) -> Dict[
        str, Any]:
        """Chia văn bản thành các đoạn nhỏ để xử lý"""
        text = await self.get_text(text_id, user)
        chunks = split_text_into_chunks(text.content, chunk_size)

        return {
            "text_id": str(text.id),
            "title": text.title,
            "total_length": len(text.content),
            "chunk_count": len(chunks),
            "chunks": chunks
        }