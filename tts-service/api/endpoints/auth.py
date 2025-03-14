from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from core.config import settings
from core.security import create_access_token, get_password_hash
from api.dependencies import authenticate_user, get_user_repository
from db.repositories.user_repository import UserRepository
from schemas.user import Token, UserCreate, UserResponse

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        user_repository: UserRepository = Depends(get_user_repository)
) -> Any:

    user = await authenticate_user(form_data.username, form_data.password, user_repository)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register_user(
        user_in: UserCreate,
        user_repository: UserRepository = Depends(get_user_repository)
) -> Any:

    user = await user_repository.get_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = await user_repository.get_by_username(user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    user_data = user_in.dict()
    user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(user_in.password)

    user = await user_repository.create(user_data)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        disabled=user.disabled
    )