from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse

from api.dependencies import get_current_active_user, get_text_repository
from db.repositories.text_repository import TextRepository
from models.user import User
from models.text import Text
from services.text_service import TextService
from schemas.text import TextCreate, TextUpdate, TextResponse
from utils.file_processor import process_uploaded_file, detect_text_language

router = APIRouter()


@router.get("/", response_model=List[TextResponse])
async def read_texts(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:

    text_service = TextService(text_repository)
    texts = await text_service.get_user_texts(current_user, skip, limit)

    result = []
    for text in texts:
        result.append(TextResponse(
            id=str(text.id),
            user_id=str(text.user_id),
            title=text.title,
            content=text.content,
            language=text.language,
            tags=text.tags,
            status=text.status,
            word_count=text.word_count,
            processing_error=text.processing_error,
            created_at=text.created_at.isoformat(),
            updated_at=text.updated_at.isoformat()
        ))

    return result


@router.post("/", response_model=TextResponse)
async def create_text(
        text_in: TextCreate,
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:

    text_service = TextService(text_repository)
    text = await text_service.create_text(text_in, current_user)

    return TextResponse(
        id=str(text.id),
        user_id=str(text.user_id),
        title=text.title,
        content=text.content,
        language=text.language,
        tags=text.tags,
        status=text.status,
        word_count=text.word_count,
        processing_error=text.processing_error,
        created_at=text.created_at.isoformat(),
        updated_at=text.updated_at.isoformat()
    )


@router.post("/upload", response_model=TextResponse)
async def upload_text_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        title: str = Form(None),
        language: str = Form("vi"),
        tags: str = Form(""),
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:

    try:
        file_location = f"/tmp/tts_uploads/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        file_info = await process_uploaded_file(file_location)
        content = file_info["content"]

        if not language:
            language = await detect_text_language(content)

        if not title:
            title = file.filename

        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        text_in = TextCreate(
            title=title,
            content=content,
            language=language,
            tags=tag_list
        )

        text_service = TextService(text_repository)
        text = await text_service.create_text(text_in, current_user)

        return TextResponse(
            id=str(text.id),
            user_id=str(text.user_id),
            title=text.title,
            content=text.content,
            language=text.language,
            tags=text.tags,
            status=text.status,
            word_count=text.word_count,
            processing_error=text.processing_error,
            created_at=text.created_at.isoformat(),
            updated_at=text.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/{text_id}", response_model=TextResponse)
async def read_text(
        text_id: str,
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:
    text_service = TextService(text_repository)
    text = await text_service.get_text(text_id, current_user)

    return TextResponse(
        id=str(text.id),
        user_id=str(text.user_id),
        title=text.title,
        content=text.content,
        language=text.language,
        tags=text.tags,
        status=text.status,
        word_count=text.word_count,
        processing_error=text.processing_error,
        created_at=text.created_at.isoformat(),
        updated_at=text.updated_at.isoformat()
    )


@router.put("/{text_id}", response_model=TextResponse)
async def update_text(
        text_id: str,
        text_in: TextUpdate,
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:
    text_service = TextService(text_repository)
    text = await text_service.update_text(text_id, text_in, current_user)

    return TextResponse(
        id=str(text.id),
        user_id=str(text.user_id),
        title=text.title,
        content=text.content,
        language=text.language,
        tags=text.tags,
        status=text.status,
        word_count=text.word_count,
        processing_error=text.processing_error,
        created_at=text.created_at.isoformat(),
        updated_at=text.updated_at.isoformat()
    )


@router.delete("/{text_id}")
async def delete_text(
        text_id: str,
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:

    text_service = TextService(text_repository)
    success = await text_service.delete_text(text_id, current_user)

    if success:
        return JSONResponse(content={"message": "Text deleted successfully"})

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error deleting text"
    )


@router.get("/{text_id}/chunks")
async def get_text_chunks(
        text_id: str,
        chunk_size: Optional[int] = None,
        current_user: User = Depends(get_current_active_user),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:
    text_service = TextService(text_repository)
    chunks = await text_service.split_text_into_chunks(text_id, current_user, chunk_size)

    return chunks