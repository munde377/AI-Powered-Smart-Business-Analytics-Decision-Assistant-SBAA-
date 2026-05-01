"""Data validation and cleaning pipeline for uploaded datasets."""
import pandas as pd
import numpy as np
from typing import Any, Tuple, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Validate and clean pandas DataFrames."""
    
    @staticmethod
    def validate_file_format(filename: str) -> bool:
        """Check if file is valid CSV or Excel format."""
        valid_extensions = ['.csv', '.xlsx', '.xls']
        ext = ''.join(filename.split('.')[-1:]).lower()
        return f'.{ext}' in valid_extensions

    @staticmethod
    def load_file(file_path: str) -> pd.DataFrame:
        """Load CSV or Excel file into DataFrame."""
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        return df

    @staticmethod
    def get_data_types_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of data types in DataFrame."""
        dtypes = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if dtype.startswith('int'):
                dtypes[col] = 'integer'
            elif dtype.startswith('float'):
                dtypes[col] = 'float'
            elif dtype == 'object':
                dtypes[col] = 'string'
            elif dtype.startswith('datetime'):
                dtypes[col] = 'datetime'
            elif dtype == 'bool':
                dtypes[col] = 'boolean'
            else:
                dtypes[col] = dtype
        return dtypes

    @staticmethod
    def get_missing_values(df: pd.DataFrame) -> Dict[str, int]:
        """Get count of missing values per column."""
        return df.isnull().sum().to_dict()

    @staticmethod
    def get_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for numeric columns."""
        stats = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            stats[col] = {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std()),
                'count': int(df[col].count()),
            }
        return stats

class DataCleaner:
    """Clean and preprocess pandas DataFrames."""
    
    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names."""
        df = df.copy()
        df.columns = [
            str(col)
            .strip()
            .lower()
            .replace(' ', '_')
            .replace('-', '_')
            .replace('(', '')
            .replace(')', '')
            .replace('/', '_')
            for col in df.columns
        ]
        return df

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: List[str] = None) -> Tuple[pd.DataFrame, int]:
        """Remove duplicate rows."""
        initial_len = len(df)
        df = df.drop_duplicates(subset=subset).reset_index(drop=True)
        removed = initial_len - len(df)
        return df, removed

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = 'drop') -> pd.DataFrame:
        """Handle missing values in DataFrame."""
        df = df.copy()
        
        if strategy == 'drop':
            df = df.dropna()
        elif strategy == 'drop_columns':
            df = df.dropna(axis=1, how='all')
        elif strategy == 'fill_numeric':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            
            object_cols = df.select_dtypes(include=['object']).columns
            df[object_cols] = df[object_cols].fillna('Unknown')
        elif strategy == 'forward_fill':
            df = df.fillna(method='ffill').fillna(method='bfill')
        
        return df.reset_index(drop=True)

    @staticmethod
    def convert_dtypes(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Intelligently convert data types."""
        df = df.copy()
        conversions = {}
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to datetime
                try:
                    df[col] = pd.to_datetime(df[col])
                    conversions[col] = 'datetime'
                    continue
                except (ValueError, TypeError):
                    pass
                
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].isnull().sum() < len(df) * 0.5:  # If not too many nulls
                        conversions[col] = 'numeric'
                        continue
                except (ValueError, TypeError):
                    pass
                
                conversions[col] = 'string'
        
        return df, conversions

    @staticmethod
    def remove_outliers(df: pd.DataFrame, threshold: float = 3.0) -> Tuple[pd.DataFrame, int]:
        """Remove statistical outliers using z-score."""
        df = df.copy()
        initial_len = len(df)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            df = df[z_scores < threshold]
        
        df = df.reset_index(drop=True)
        removed = initial_len - len(df)
        return df, removed

    @staticmethod
    def normalize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numeric columns to 0-1 range."""
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:
                df[col] = (df[col] - min_val) / (max_val - min_val)
        
        return df

class DataProcessor:
    """Orchestrate data validation and cleaning."""
    
    @staticmethod
    def load_dataframe(file_path: str) -> pd.DataFrame:
        """Load a DataFrame from a CSV or Excel file."""
        return DataValidator.load_file(file_path)

    @staticmethod
    def process_uploaded_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Process uploaded file with full cleaning pipeline."""
        logger.info(f'Processing file: {file_path}')
        
        # Load file
        df = DataValidator.load_file(file_path)
        logger.info(f'Loaded {len(df)} rows, {len(df.columns)} columns')
        
        # Get initial stats
        initial_stats = {
            'raw_rows': len(df),
            'raw_columns': len(df.columns),
            'raw_columns_list': df.columns.tolist(),
            'raw_dtypes': DataValidator.get_data_types_summary(df),
            'raw_missing': DataValidator.get_missing_values(df),
        }
        
        # Clean column names
        df = DataCleaner.clean_column_names(df)
        
        # Remove duplicate rows
        df, dup_removed = DataCleaner.remove_duplicates(df)
        logger.info(f'Removed {dup_removed} duplicate rows')
        
        # Handle missing values
        df = DataCleaner.handle_missing_values(df, strategy='drop_columns')
        
        # Convert data types
        df, conversions = DataCleaner.convert_dtypes(df)
        logger.info(f'Converted types: {conversions}')
        
        # Remove outliers (for numeric columns only)
        df_no_outliers, outliers_removed = DataCleaner.remove_outliers(df, threshold=3.0)
        if outliers_removed > 0:
            logger.info(f'Removed {outliers_removed} outliers')
            df = df_no_outliers
        
        # Final stats
        final_stats = {
            'processed_rows': len(df),
            'processed_columns': len(df.columns),
            'columns_list': df.columns.tolist(),
            'dtypes': DataValidator.get_data_types_summary(df),
            'missing_values': DataValidator.get_missing_values(df),
            'summary_statistics': DataValidator.get_summary_statistics(df),
            'processing_log': {
                'duplicates_removed': dup_removed,
                'outliers_removed': outliers_removed,
                'type_conversions': conversions,
            }
        }
        
        logger.info(f'Processing complete: {len(df)} rows, {len(df.columns)} columns')
        return df, final_stats
