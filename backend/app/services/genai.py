"""GenAI service for natural language to SQL conversion and chat with data using Groq."""
import json
import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import groq
from groq import Groq

from ..config import settings
from ..models.dataset import Dataset
from ..models.chat import ChatHistory
from ..core.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class GenAIService:
    """GenAI service for chat with data using the Groq API."""

    @staticmethod
    def get_groq_client() -> Groq:
        if not settings.groq_api_key:
            raise ValueError('GROQ_API_KEY must be set for GenAI requests')

        try:
            return Groq(
                api_key=settings.groq_api_key,
                timeout=60.0,
                max_retries=2,
            )
        except Exception as exc:
            logger.error('Failed to initialize Groq client: %s', exc)
            raise ValueError('Unable to initialize Groq client') from exc

    @staticmethod
    def _groq_chat(messages: List[Dict[str, str]], model: str) -> str:
        client = GenAIService.get_groq_client()

        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
            )
            content = getattr(response.choices[0].message, 'content', None)
            if not content:
                raise ValueError('Groq returned an empty response')
            return str(content).strip()

        except groq.APITimeoutError as exc:
            logger.error('Groq timeout: %s', exc)
            raise ValueError('Groq API request timed out. Please try again later.') from exc
        except groq.RateLimitError as exc:
            logger.error('Groq rate limit: %s', exc)
            raise ValueError('Groq API rate limit reached. Please wait a moment and retry.') from exc
        except groq.APIConnectionError as exc:
            logger.error('Groq connection failed: %s', exc)
            raise ValueError('Unable to connect to Groq API. Check the network and API key.') from exc
        except groq.APIError as exc:
            logger.error('Groq API error: %s', exc)
            status_code = getattr(exc, 'status_code', None)
            message = str(exc)
            if status_code:
                message = f'Groq API error ({status_code}): {message}'
            raise ValueError(message) from exc
        except Exception as exc:
            logger.error('Unexpected Groq error: %s', exc)
            raise ValueError('Unexpected GenAI error. Please try again later.') from exc

    @staticmethod
    def load_dataset_sample(dataset: Dataset) -> str:
        """Load dataset sample for prompt context."""
        df = DataProcessor.load_dataframe(dataset.file_path)
        sample_data = df.head(20).fillna('').astype(str).to_dict('records')
        columns_info = f'Columns: {", ".join(df.columns.tolist())}\n'
        columns_info += f'Data types: {df.dtypes.to_dict()}\n'
        columns_info += f'Sample rows: {json.dumps(sample_data[:5], indent=2)}'
        return columns_info

    @staticmethod
    def natural_language_to_sql(query: str, dataset: Dataset) -> str:
        """Convert natural language query into a SQL statement."""
        logger.info('Converting NL to SQL: %s', query)

        dataset_info = GenAIService.load_dataset_sample(dataset)
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a SQL expert. Generate a single valid SQL SELECT query given the dataset schema and the natural language request. '
                    'Use the dataset column names exactly and return only the SQL query with no explanation, commentary, or markdown formatting.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Dataset information:\n{dataset_info}\n\n'
                    f'Natural language query: {query}\n\n'
                    'Return only the SQL query that answers this request.'
                ),
            },
        ]

        sql_query = GenAIService._groq_chat(messages, model=settings.groq_model)
        if sql_query.startswith('```'):
            sql_query = sql_query.strip('`')
        return sql_query.strip()

    @staticmethod
    def execute_sql_query(db: Session, sql_query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return structured results."""
        try:
            result = db.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error('SQL execution failed: %s', exc)
            raise ValueError(f'SQL execution failed: {str(exc)}') from exc

    @staticmethod
    def chat_with_data(db: Session, query: str, dataset_id: int, user_id: int) -> Dict[str, Any]:
        """Chat with dataset using Groq-based SQL generation and answer synthesis."""
        logger.info('Chat with data: %s for dataset %s', query, dataset_id)

        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError('Dataset not found')

        sql_query = GenAIService.natural_language_to_sql(query, dataset)
        try:
            sql_results = GenAIService.execute_sql_query(db, sql_query)
        except Exception as exc:
            logger.warning('SQL execution failed: %s', exc)
            sql_results = []
            sql_query = 'SELECT * FROM datasets LIMIT 10'

        dataset_context = GenAIService.load_dataset_sample(dataset)
        results_preview = json.dumps(sql_results[:10], default=str, indent=2)

        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a business analytics assistant. Answer clearly and concisely based on the dataset schema, query, and SQL results. '
                    'If the SQL query failed or produced no results, explain what happened and suggest next steps.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Dataset: {dataset.filename}\n'
                    f'Query: {query}\n'
                    f'Generated SQL: {sql_query}\n'
                    f'SQL results: {results_preview}\n\n'
                    f'Dataset sample: {dataset_context}\n\n'
                    'Provide a data-driven answer to the query, and make it easy to understand for a business user.'
                ),
            },
        ]

        answer_text = GenAIService._groq_chat(messages, model=settings.groq_model)

        chat_entry = ChatHistory(
            user_id=user_id,
            dataset_id=dataset_id,
            user_query=query,
            ai_response=answer_text,
            generated_sql=sql_query,
            metadata={
                'results_count': len(sql_results),
                'model_used': settings.groq_model,
            },
        )
        db.add(chat_entry)
        db.commit()

        return {
            'answer': answer_text,
            'sql': sql_query,
            'results': sql_results,
            'metadata': {
                'dataset_id': dataset_id,
                'results_count': len(sql_results),
                'model_used': settings.groq_model,
            },
        }
