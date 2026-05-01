import os
import json
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile
from ..models.dataset import Dataset
from ..core.utils import save_upload_file, generate_filename
from ..core.data_processor import DataProcessor, DataValidator, DataCleaner
import logging

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage')
os.makedirs(DATA_DIR, exist_ok=True)

class DatasetService:
    """Service for managing datasets."""

    @staticmethod
    def create_dataset(db: Session, name: str, filename: str, file_path: str, user_id: int) -> Dataset:
        """Create dataset record in database."""
        dataset = Dataset(
            name=name,
            filename=filename,
            file_path=file_path,
            user_id=user_id,
            status='received'
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def get_dataset(db: Session, dataset_id: int) -> Dataset | None:
        """Get dataset by ID."""
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()

    @staticmethod
    def list_datasets(db: Session, user_id: int | None = None, skip: int = 0, limit: int = 20):
        """List datasets with pagination."""
        query = db.query(Dataset)
        if user_id:
            query = query.filter(Dataset.user_id == user_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return {'items': items, 'total': total, 'skip': skip, 'limit': limit}

    @staticmethod
    def save_uploaded_file(upload_file: UploadFile, user_id: int) -> tuple[str, str]:
        """Save uploaded file to storage directory."""
        save_name = generate_filename(upload_file.filename)
        file_path = save_upload_file(upload_file, save_name)
        return save_name, file_path

    @staticmethod
    def process_dataset_file(db: Session, dataset_id: int) -> None:
        """Process and clean dataset file."""
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                logger.warning(f'Dataset {dataset_id} not found')
                return

            if not os.path.exists(dataset.file_path):
                dataset.status = 'missing'
                db.commit()
                logger.error(f'File not found: {dataset.file_path}')
                return

            # Process file with data pipeline
            df, stats = DataProcessor.process_uploaded_file(dataset.file_path)

            # Update dataset with processed data
            dataset.row_count = stats['processed_rows']
            dataset.column_count = stats['processed_columns']
            dataset.columns_list = stats['columns_list']
            dataset.dtypes = stats['dtypes']
            dataset.missing_values = stats['missing_values']
            dataset.summary_stats = stats['summary_statistics']
            dataset.metadata_json = {
                'columns': stats['columns_list'],
                'dtypes': stats['dtypes'],
                'row_count': stats['processed_rows'],
                'column_count': stats['processed_columns'],
            }
            dataset.status = 'processed'

            db.commit()
            logger.info(f'Dataset {dataset_id} processed successfully')

        except Exception as e:
            logger.error(f'Error processing dataset {dataset_id}: {str(e)}')
            dataset.status = 'failed'
            dataset.notes = f'Processing error: {str(e)}'
            db.commit()

    @staticmethod
    def load_dataset(dataset: Dataset) -> pd.DataFrame:
        """Load processed dataset from file."""
        if dataset.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(dataset.file_path)
        else:
            df = pd.read_csv(dataset.file_path)
        return df

    @staticmethod
    def get_dataset_preview(db: Session, dataset_id: int, rows: int = 5) -> list[dict]:
        """Get preview of dataset rows."""
        dataset = DatasetService.get_dataset(db, dataset_id)
        if not dataset:
            return []

        try:
            df = DatasetService.load_dataset(dataset)
            return df.head(rows).to_dict(orient='records')
        except Exception as e:
            logger.error(f'Error getting preview for dataset {dataset_id}: {str(e)}')
            return []

    @staticmethod
    def delete_dataset(db: Session, dataset_id: int) -> bool:
        """Delete dataset and associated file."""
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return False

        try:
            if os.path.exists(dataset.file_path):
                os.remove(dataset.file_path)
        except Exception as e:
            logger.warning(f'Could not delete file {dataset.file_path}: {str(e)}')

        db.delete(dataset)
        db.commit()
        return True
