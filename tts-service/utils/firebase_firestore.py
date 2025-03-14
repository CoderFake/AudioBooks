import os
import json
import base64
import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

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
        firebase_admin.initialize_app(cred)

        logger.info("Firebase app initialized successfully")


async def upload_audio_to_firestore(local_file_path: str, collection_path: str, document_id: str) -> str:
    try:
        initialize_firebase_app()

        db = firestore.client()

        with open(local_file_path, 'rb') as file:
            audio_bytes = file.read()

        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        audio_data = {
            'content': audio_base64,
            'filename': os.path.basename(local_file_path),
            'content_type': f'audio/{os.path.splitext(local_file_path)[1][1:]}',
            'size': len(audio_bytes),
            'uploaded_at': firestore.SERVER_TIMESTAMP
        }

        audio_ref = db.collection(collection_path).document(document_id)
        audio_ref.set(audio_data)

        firestore_url = f"firestore://{collection_path}/{document_id}"

        logger.info(f"Audio uploaded successfully to Firestore: {firestore_url}")

        return firestore_url

    except Exception as e:
        logger.exception(f"Error uploading audio to Firestore: {str(e)}")
        raise


async def upload_audio_segment_to_firestore(local_file_path: str, collection_path: str, document_id: str,
                                            segment_id: str) -> str:

    try:
        initialize_firebase_app()

        db = firestore.client()

        with open(local_file_path, 'rb') as file:
            audio_bytes = file.read()

        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        segment_data = {
            'content': audio_base64,
            'filename': os.path.basename(local_file_path),
            'content_type': f'audio/{os.path.splitext(local_file_path)[1][1:]}',
            'size': len(audio_bytes),
            'uploaded_at': firestore.SERVER_TIMESTAMP
        }

        segment_ref = db.collection(collection_path).document(document_id).collection('segments').document(segment_id)
        segment_ref.set(segment_data)

        firestore_url = f"firestore://{collection_path}/{document_id}/segments/{segment_id}"

        logger.info(f"Audio segment uploaded successfully to Firestore: {firestore_url}")

        return firestore_url

    except Exception as e:
        logger.exception(f"Error uploading audio segment to Firestore: {str(e)}")
        raise


async def delete_audio_from_firestore(firestore_url: str) -> bool:
    try:
        initialize_firebase_app()

        parts = firestore_url.replace('firestore://', '').split('/')

        db = firestore.client()

        if len(parts) == 2:
            collection_path, document_id = parts
            document_ref = db.collection(collection_path).document(document_id)
            document_ref.delete()
        elif len(parts) == 4 and parts[2] == 'segments':
            collection_path, document_id, _, segment_id = parts
            segment_ref = db.collection(collection_path).document(document_id).collection('segments').document(
                segment_id)
            segment_ref.delete()
        else:
            logger.error(f"Invalid Firestore URL format: {firestore_url}")
            return False

        logger.info(f"Audio deleted successfully from Firestore: {firestore_url}")

        return True

    except Exception as e:
        logger.exception(f"Error deleting audio from Firestore: {str(e)}")
        return False


async def download_audio_from_firestore(firestore_url: str, local_file_path: str) -> bool:
    try:
        initialize_firebase_app()

        parts = firestore_url.replace('firestore://', '').split('/')

        db = firestore.client()

        audio_data = None

        if len(parts) == 2:
            collection_path, document_id = parts
            document_ref = db.collection(collection_path).document(document_id)
            document = document_ref.get()
            if document.exists:
                audio_data = document.to_dict()
        elif len(parts) == 4 and parts[2] == 'segments':
            # Audio segment
            collection_path, document_id, _, segment_id = parts
            segment_ref = db.collection(collection_path).document(document_id).collection('segments').document(
                segment_id)
            segment = segment_ref.get()
            if segment.exists:
                audio_data = segment.to_dict()
        else:
            logger.error(f"Invalid Firestore URL format: {firestore_url}")
            return False

        if not audio_data or 'content' not in audio_data:
            logger.error(f"Audio data not found or invalid: {firestore_url}")
            return False

        os.makedirs(os.path.dirname(os.path.abspath(local_file_path)), exist_ok=True)

        audio_bytes = base64.b64decode(audio_data['content'])
        with open(local_file_path, 'wb') as file:
            file.write(audio_bytes)

        logger.info(f"Audio downloaded successfully from Firestore to: {local_file_path}")

        return True

    except Exception as e:
        logger.exception(f"Error downloading audio from Firestore: {str(e)}")
        return False


async def get_audio_metadata_from_firestore(firestore_url: str) -> Optional[Dict[str, Any]]:

    try:
        initialize_firebase_app()

        parts = firestore_url.replace('firestore://', '').split('/')

        db = firestore.client()

        audio_data = None

        if len(parts) == 2:
            collection_path, document_id = parts
            document_ref = db.collection(collection_path).document(document_id)
            document = document_ref.get()
            if document.exists:
                audio_data = document.to_dict()
        elif len(parts) == 4 and parts[2] == 'segments':
            collection_path, document_id, _, segment_id = parts
            segment_ref = db.collection(collection_path).document(document_id).collection('segments').document(
                segment_id)
            segment = segment_ref.get()
            if segment.exists:
                audio_data = segment.to_dict()
        else:
            logger.error(f"Invalid Firestore URL format: {firestore_url}")
            return None

        if not audio_data:
            logger.error(f"Audio data not found: {firestore_url}")
            return None

        metadata = {k: v for k, v in audio_data.items() if k != 'content'}

        return metadata

    except Exception as e:
        logger.exception(f"Error getting audio metadata from Firestore: {str(e)}")
        return None