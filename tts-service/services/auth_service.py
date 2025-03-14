from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.config import settings
from db.mongodb import get_database
from db.repositories.user_repository import UserRepository
from models.user import User
from schemas.user import TokenData


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Kiểm tra mật khẩu"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Băm mật khẩu"""
        return pwd_context.hash(password)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Xác thực người dùng"""
        user = await self.user_repository.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Tạo token JWT"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Lấy người dùng hiện tại từ token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")

            if username is None or user_id is None:
                raise credentials_exception

            token_data = TokenData(username=username, user_id=user_id)
        except JWTError:
            raise credentials_exception

        user = await self.user_repository.get_by_id(token_data.user_id)
        if user is None:
            raise credentials_exception

        return user


# Dependency để lấy AuthService
async def get_auth_service():
    db = get_database()
    user_repository = UserRepository(db)
    return AuthService(user_repository)


# Dependency để lấy current user (người dùng hiện tại)
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.get_current_user(token)


# Dependency để kiểm tra người dùng có bị disabled không
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Dependency để kiểm tra người dùng có phải admin không
async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user