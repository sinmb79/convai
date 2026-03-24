import uuid
from pathlib import Path
from typing import Optional
from supabase import create_client, Client
from app.config import settings


def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def upload_file(
    file_bytes: bytes,
    project_id: str,
    file_type: str,
    filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload file to Supabase Storage. Returns storage path (s3_key)."""
    client = get_supabase()
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4()}{ext}"
    path = f"{project_id}/{file_type}/{unique_name}"

    client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
        path,
        file_bytes,
        file_options={"content-type": content_type},
    )
    return path


def get_download_url(s3_key: str, expires_in: int = 3600) -> str:
    """Get a presigned download URL."""
    client = get_supabase()
    response = client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).create_signed_url(
        s3_key, expires_in
    )
    return response["signedURL"]


def delete_file(s3_key: str) -> None:
    client = get_supabase()
    client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).remove([s3_key])
