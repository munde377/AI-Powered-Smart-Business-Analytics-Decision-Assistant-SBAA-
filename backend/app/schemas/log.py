from datetime import datetime
from pydantic import BaseModel
from typing import Any

class PredictionLogRead(BaseModel):
    id: int
    user_id: int | None
    model_id: int | None
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    comment: str | None
    created_at: datetime

    class Config:
        orm_mode = True
