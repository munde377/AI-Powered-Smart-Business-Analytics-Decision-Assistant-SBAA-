from pydantic import BaseModel
from typing import Any

class ChatRequest(BaseModel):
    query: str
    dataset_id: int | None = None

class ChatResponse(BaseModel):
    answer: str
    sql: str | None = None
    metadata: dict[str, Any] | None = None
