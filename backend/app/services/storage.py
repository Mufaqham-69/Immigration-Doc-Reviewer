"""
File storage abstraction. MVP uses local disk; swap this module for an S3/R2
client when you need multi-instance deployment. Nothing outside this file
needs to change - routes and workers only call save_upload() / read_file().
"""
import os
import uuid

from app.core.config import get_settings

settings = get_settings()


def save_upload(file_bytes: bytes, original_filename: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1]
    stored_name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def read_file(storage_path: str) -> bytes:
    with open(storage_path, "rb") as f:
        return f.read()
