"""GenAI API endpoints for chat with data."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from ..database import get_db
from ..services.genai import GenAIService
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.chat import ChatHistory

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    """Request for chat with data."""
    query: str
    dataset_id: int

class ChatResponse(BaseModel):
    """Response from chat with data."""
    answer: str
    sql: str
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class SQLTranslateRequest(BaseModel):
    """Request for SQL translation."""
    query: str
    dataset_id: int

class SQLTranslateResponse(BaseModel):
    """Response from SQL translation."""
    sql: str

@router.post('/chat', response_model=ChatResponse)
def chat_with_data(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Chat with dataset using natural language."""
    try:
        result = GenAIService.chat_with_data(
            db=db,
            query=request.query,
            dataset_id=request.dataset_id,
            user_id=current_user.id
        )
        
        logger.info(f'User {current_user.id} chatted with dataset {request.dataset_id}: {request.query[:50]}...')
        
        return ChatResponse(
            answer=result['answer'],
            sql=result['sql'],
            results=result['results'],
            metadata=result['metadata']
        )
    
    except Exception as e:
        logger.error(f'Chat failed: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Chat failed: {str(e)}'
        )

@router.post('/translate-sql', response_model=SQLTranslateResponse)
def translate_to_sql(
    request: SQLTranslateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Translate natural language to SQL query."""
    try:
        from ..models.dataset import Dataset
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail='Dataset not found')
        
        sql_query = GenAIService.natural_language_to_sql(request.query, dataset)
        
        logger.info(f'User {current_user.id} translated query to SQL for dataset {request.dataset_id}')
        
        return SQLTranslateResponse(sql=sql_query)
    
    except Exception as e:
        logger.error(f'SQL translation failed: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'SQL translation failed: {str(e)}'
        )

@router.get('/chat-history', response_model=List[Dict[str, Any]])
def get_chat_history(
    dataset_id: int = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history."""
    query = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id)
    if dataset_id:
        # Note: ChatHistory doesn't have dataset_id, but we can filter by query content or add it later
        pass
    
    chats = query.offset(skip).limit(limit).all()
    return [
        {
            'id': chat.id,
            'query': chat.user_query,
            'response': chat.ai_response,
            'sql_query': chat.generated_sql,
            'results_count': chat.metadata_json.get('results_count', 0) if chat.metadata_json else 0,
            'created_at': chat.created_at.isoformat()
        }
        for chat in chats
    ]
