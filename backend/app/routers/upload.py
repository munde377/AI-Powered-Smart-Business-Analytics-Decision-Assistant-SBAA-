from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.dataset import DatasetService
from ..schemas.dataset import DatasetRead, DatasetListResponse
from ..core.security import get_current_active_user
from ..models.user import User
from ..tasks.workers import process_dataset

router = APIRouter()

ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

@router.post('/upload', response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload dataset file (CSV or Excel)."""
    # Validate file extension
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        )

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f'File size exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f} MB limit'
        )

    try:
        # Save file and create dataset record
        save_name, file_path = DatasetService.save_uploaded_file(file, current_user.id)
        dataset = DatasetService.create_dataset(
            db,
            name=file.filename.split('.')[0],
            filename=save_name,
            file_path=file_path,
            user_id=current_user.id
        )

        # Queue background processing task
        process_dataset.delay(dataset.id)

        return dataset

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Upload failed: {str(e)}'
        )

@router.get('/', response_model=DatasetListResponse)
def list_datasets(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's datasets with pagination."""
    result = DatasetService.list_datasets(db, user_id=current_user.id, skip=skip, limit=limit)
    return DatasetListResponse(**result)

@router.get('/{dataset_id}', response_model=DatasetRead)
def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific dataset details."""
    dataset = DatasetService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Dataset not found')
    
    if dataset.user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    
    return dataset

@router.get('/{dataset_id}/preview')
def get_dataset_preview(
    dataset_id: int,
    rows: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dataset preview (first N rows)."""
    dataset = DatasetService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Dataset not found')
    
    if dataset.user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    
    preview = DatasetService.get_dataset_preview(db, dataset_id, rows=rows)
    return {'data': preview}

@router.delete('/{dataset_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete dataset."""
    dataset = DatasetService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Dataset not found')
    
    if dataset.user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    
    DatasetService.delete_dataset(db, dataset_id)
