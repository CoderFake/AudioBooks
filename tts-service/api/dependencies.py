from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from core.config import settings
from core.security import verify_password
from db.mongodb import get_database
from db.repositories.user_repository import UserRepository
from db.repositories.text_repository import TextRepository
from db.repositories.audio_repository import AudioRepository
from models.user import User
from schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# Dependency để lấy UserRepository
async def get_user_repository():
    db = get_database()
    return UserRepository(db)


# Dependency để lấy TextRepository
async def get_text_repository():
    db = get_database()
    return TextRepository(db)


# Dependency để lấy AudioRepository
async def get_audio_repository():
    db = get_database()
    return AudioRepository(db)


# Verify token và lấy thông tin user
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        user_repository: UserRepository = Depends(get_user_repository)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")

        if username is None or user_id is None:
            raise credentials_exception

        token_data = TokenData(username=username, user_id=user_id)
    except (JWTError, ValidationError):
        raise credentials_exception

    user = await user_repository.get_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
        current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def authenticate_user(
        username: str,
        password: str,
        user_repository: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    user = await user_repository.get_by_username(username)
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user