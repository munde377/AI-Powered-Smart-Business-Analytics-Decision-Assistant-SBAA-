from datetime import datetime
from pydantic import BaseModel
from typing import Any

class DatasetCreate(BaseModel):
    """Schema for dataset creation."""
    name: str
    notes: str | None = None

class DatasetMetadata(BaseModel):
    """Schema for dataset metadata."""
    columns: list[str]
    dtypes: dict[str, str]
    row_count: int
    column_count: int
    missing_values: dict[str, int]
    preview: list[dict[str, Any]] | None = None

class DatasetSummary(BaseModel):
    """Schema for dataset summary statistics."""
    columns_list: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    summary_statistics: dict[str, Any]
    processing_log: dict[str, Any]

class DatasetRead(BaseModel):
    """Schema for dataset response."""
    id: int
    user_id: int
    name: str
    filename: str
    row_count: int
    column_count: int
    status: str
    metadata: dict[str, Any] | None
    summary_stats: dict[str, Any] | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DatasetListResponse(BaseModel):
    """Schema for dataset list response."""
    items: list[DatasetRead]
    total: int
    skip: int
    limit: int
