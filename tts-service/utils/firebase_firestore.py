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
        service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')

        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase app initialized successfully from service account file")
        else:
            logger.warning("Firebase service account file not found. Using local file storage.")
            os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'local_storage'), exist_ok=True)


async def upload_audio_to_firestore(local_file_path: str, collection_path: str, document_id: str) -> str:
    try:
        try:
            initialize_firebase_app()

            service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
            if not os.path.exists(service_account_path):
                local_storage_dir = os.path.join(os.path.dirname(__file__), '..', 'local_storage')
                document_path = os.path.join(local_storage_dir, f"{document_id}.audio")

                with open(local_file_path, 'rb') as src, open(document_path, 'wb') as dst:
                    dst.write(src.read())

                logger.info(f"File stored locally at: {document_path}")
                return f"local://{document_path}"

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

        except Exception as firebase_error:
            logger.warning(f"Firebase initialization error: {str(firebase_error)}. Using local storage.")

            local_storage_dir = os.path.join(os.path.dirname(__file__), '..', 'local_storage')
            os.makedirs(local_storage_dir, exist_ok=True)
            document_path = os.path.join(local_storage_dir, f"{document_id}.audio")

            with open(local_file_path, 'rb') as src, open(document_path, 'wb') as dst:
                dst.write(src.read())

            logger.info(f"File stored locally at: {document_path}")
            return f"local://{document_path}"

    except Exception as e:
        logger.exception(f"Error uploading audio: {str(e)}")
        return f"file://{local_file_path}"


async def upload_audio_segment_to_firestore(local_file_path: str, collection_path: str, document_id: str,
                                            segment_id: str) -> str:
    try:
        try:
            initialize_firebase_app()

            service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
            if not os.path.exists(service_account_path):
                local_storage_dir = os.path.join(os.path.dirname(__file__), '..', 'local_storage', document_id)
                os.makedirs(local_storage_dir, exist_ok=True)
                segment_path = os.path.join(local_storage_dir, f"{segment_id}.audio")

                with open(local_file_path, 'rb') as src, open(segment_path, 'wb') as dst:
                    dst.write(src.read())

                logger.info(f"Segment stored locally at: {segment_path}")
                return f"local://{segment_path}"

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

            segment_ref = db.collection(collection_path).document(document_id).collection('segments').document(
                segment_id)
            segment_ref.set(segment_data)

            firestore_url = f"firestore://{collection_path}/{document_id}/segments/{segment_id}"

            logger.info(f"Audio segment uploaded successfully to Firestore: {firestore_url}")

            return firestore_url

        except Exception as firebase_error:
            logger.warning(f"Firebase initialization error: {str(firebase_error)}. Using local storage.")

            local_storage_dir = os.path.join(os.path.dirname(__file__), '..', 'local_storage', document_id)
            os.makedirs(local_storage_dir, exist_ok=True)
            segment_path = os.path.join(local_storage_dir, f"{segment_id}.audio")

            with open(local_file_path, 'rb') as src, open(segment_path, 'wb') as dst:
                dst.write(src.read())

            logger.info(f"Segment stored locally at: {segment_path}")
            return f"local://{segment_path}"

    except Exception as e:
        logger.exception(f"Error uploading audio segment: {str(e)}")
        return f"file://{local_file_path}"


async def delete_audio_from_firestore(firestore_url: str) -> bool:
    if firestore_url.startswith("local://") or firestore_url.startswith("file://"):
        file_path = firestore_url.replace("local://", "").replace("file://", "")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted local file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting local file {file_path}: {str(e)}")
            return False

    try:
        initialize_firebase_app()

        service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
        if not os.path.exists(service_account_path):
            logger.warning("Firebase not configured. Cannot delete from Firestore.")
            return False

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
    if firestore_url.startswith("local://") or firestore_url.startswith("file://"):
        source_path = firestore_url.replace("local://", "").replace("file://", "")
        try:
            os.makedirs(os.path.dirname(os.path.abspath(local_file_path)), exist_ok=True)
            if os.path.exists(source_path):
                with open(source_path, 'rb') as src, open(local_file_path, 'wb') as dst:
                    dst.write(src.read())
                logger.info(f"Copied local file from {source_path} to {local_file_path}")
                return True
            else:
                logger.error(f"Source file does not exist: {source_path}")
                return False
        except Exception as e:
            logger.error(f"Error copying local file {source_path}: {str(e)}")
            return False

    try:
        initialize_firebase_app()

        service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
        if not os.path.exists(service_account_path):
            logger.warning("Firebase not configured. Cannot download from Firestore.")
            return False

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
    if firestore_url.startswith("local://") or firestore_url.startswith("file://"):
        file_path = firestore_url.replace("local://", "").replace("file://", "")
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                return {
                    "filename": filename,
                    "size": file_size,
                    "content_type": f"audio/{os.path.splitext(filename)[1][1:]}",
                    "uploaded_at": datetime.fromtimestamp(os.path.getmtime(file_path))
                }
            else:
                logger.error(f"File does not exist: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error getting metadata for local file {file_path}: {str(e)}")
            return None

    try:
        initialize_firebase_app()

        service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
        if not os.path.exists(service_account_path):
            logger.warning("Firebase not configured. Cannot get metadata from Firestore.")
            return None

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