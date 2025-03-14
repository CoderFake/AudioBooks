import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, storage
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)


def initialize_firebase_app():
    try:

        firebase_admin.get_app()
    except ValueError:
        cred_info = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
        }

        cred = credentials.Certificate(cred_info)
        firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_STORAGE_BUCKET
        })

        logger.info("Firebase app initialized successfully")


async def upload_file_to_firebase(local_file_path: str, firebase_path: str) -> str:
    try:
        initialize_firebase_app()

        bucket = storage.bucket()

        blob = bucket.blob(firebase_path)

        logger.info(f"Uploading file to Firebase Storage: {firebase_path}")
        blob.upload_from_filename(local_file_path)

        blob.make_public()

        url = blob.public_url

        logger.info(f"File uploaded successfully to Firebase Storage: {url}")

        return url
    except Exception as e:
        logger.exception(f"Error uploading file to Firebase Storage: {str(e)}")
        raise


async def delete_file_from_firebase(firebase_url: str) -> bool:
    try:
        initialize_firebase_app()

        bucket = storage.bucket()

        path = firebase_url.split(f"https://storage.googleapis.com/{settings.FIREBASE_STORAGE_BUCKET}/")[1]

        blob = bucket.blob(path)

        logger.info(f"Deleting file from Firebase Storage: {path}")
        blob.delete()

        logger.info(f"File deleted successfully from Firebase Storage: {path}")

        return True
    except Exception as e:
        logger.exception(f"Error deleting file from Firebase Storage: {str(e)}")
        return False


async def get_file_metadata_from_firebase(firebase_url: str) -> Optional[dict]:

    try:
        initialize_firebase_app()

        bucket = storage.bucket()

        path = firebase_url.split(f"https://storage.googleapis.com/{settings.FIREBASE_STORAGE_BUCKET}/")[1]

        blob = bucket.blob(path)

        blob.reload()
        metadata = blob.metadata

        return metadata
    except Exception as e:
        logger.exception(f"Error getting file metadata from Firebase Storage: {str(e)}")
        return None


async def download_file_from_firebase(firebase_url: str, local_file_path: str) -> bool:
    try:
        initialize_firebase_app()

        bucket = storage.bucket()

        path = firebase_url.split(f"https://storage.googleapis.com/{settings.FIREBASE_STORAGE_BUCKET}/")[1]

        blob = bucket.blob(path)

        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        logger.info(f"Downloading file from Firebase Storage: {path}")
        blob.download_to_filename(local_file_path)

        logger.info(f"File downloaded successfully from Firebase Storage: {local_file_path}")

        return True
    except Exception as e:
        logger.exception(f"Error downloading file from Firebase Storage: {str(e)}")
        return False