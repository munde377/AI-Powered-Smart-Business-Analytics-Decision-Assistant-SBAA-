"""Utility functions for the backend."""
import os
import pandas as pd
from datetime import datetime
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to storage directory."""
    file_path = os.path.join(UPLOAD_DIR, destination)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'wb') as buffer:
        buffer.write(upload_file.file.read())
    
    logger.info(f'Saved file to: {file_path}')
    return file_path

def generate_filename(original_name: str) -> str:
    """Generate unique filename with timestamp."""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]
    name_part = original_name.rsplit('.', 1)[0].replace(' ', '_')
    ext = original_name.rsplit('.', 1)[1] if '.' in original_name else 'txt'
    return f'{timestamp}_{name_part}.{ext}'

def get_storage_dir() -> str:
    """Get storage directory path."""
    return UPLOAD_DIR

def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def delete_file(file_path: str) -> bool:
    """Delete file if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f'Deleted file: {file_path}')
            return True
    except Exception as e:
        logger.error(f'Error deleting file {file_path}: {str(e)}')
    return False

def format_bytes(bytes_size: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f'{bytes_size:.2f} {unit}'
        bytes_size /= 1024.0
    return f'{bytes_size:.2f} TB'
