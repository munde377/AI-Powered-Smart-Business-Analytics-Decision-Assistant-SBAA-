from pydantic import BaseModel
from typing import Any

class TrainRequest(BaseModel):
    dataset_id: int
    target_column: str
    feature_columns: list[str] | None = None
    model_name: str
    model_type: str

class PredictRequest(BaseModel):
    model_id: int
    record: dict[str, Any]

class ForecastRequest(BaseModel):
    dataset_id: int
    lookback_steps: int = 12
    forecast_steps: int = 6
    target_column: str

class ModelMetaRead(BaseModel):
    id: int
    name: str
    model_type: str
    trained_by: int
    accuracy: float | None
    model_path: str
    params: dict[str, Any] | None

    class Config:
        orm_mode = True
