"""Machine Learning pipeline for regression and classification models."""
import os
import json
import numpy as np
import joblib
import pandas as pd
import logging
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from sqlalchemy.orm import Session
from ..models.model_meta import ModelMeta
from ..models.dataset import Dataset
from ..core.data_processor import DataProcessor

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage')
MODEL_DIR = os.path.join(DATA_DIR, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

class MLPreprocessor:
    """Data preprocessing for ML models."""
    
    @staticmethod
    def detect_numeric_categorical_columns(df: pd.DataFrame) -> Tuple[list, list]:
        """Separate numeric and categorical columns."""
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        return numeric_cols, categorical_cols
    
    @staticmethod
    def create_preprocessor(numeric_cols: list, categorical_cols: list) -> ColumnTransformer:
        """Create preprocessing pipeline."""
        transformers = []
        if numeric_cols:
            transformers.append(('num', StandardScaler(), numeric_cols))
        if categorical_cols:
            transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols))

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder='passthrough'
        )
        return preprocessor
    
    @staticmethod
    def preprocess_data(df: pd.DataFrame, target_col: str, feature_cols: Optional[list] = None) -> Tuple[np.ndarray, np.ndarray, list]:
        """Preprocess data for training."""
        df = df.copy()
        
        # Handle missing values
        df = df.dropna(subset=[target_col])
        
        # Select features
        if feature_cols is None:
            feature_cols = [c for c in df.columns if c != target_col]
        else:
            feature_cols = [c for c in feature_cols if c in df.columns and c != target_col]
        
        X = df[feature_cols].fillna(0)
        y = df[target_col].fillna(0)
        
        # Detect column types
        numeric_cols, categorical_cols = MLPreprocessor.detect_numeric_categorical_columns(X)
        
        # Build preprocessor for raw features
        preprocessor = MLPreprocessor.create_preprocessor(numeric_cols, categorical_cols)
        
        return X, y.values, feature_cols, preprocessor

class MLPipeline:
    """Complete ML pipeline for model training and prediction."""
    
    @staticmethod
    def load_dataset(dataset: Dataset) -> pd.DataFrame:
        """Load dataset from file."""
        file_path = dataset.file_path
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        return df
    
    @staticmethod
    def train_regression_model(
        db: Session,
        dataset_id: int,
        target_column: str,
        feature_columns: Optional[list],
        model_name: str,
        model_type: str,
        user_id: int,
        algorithm: str = 'randomforest'
    ) -> ModelMeta:
        """Train regression model."""
        logger.info(f'Training {algorithm} regression model: {model_name}')
        
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError('Dataset not found')
        
        df = MLPipeline.load_dataset(dataset)
        if target_column not in df.columns:
            raise ValueError(f'Target column "{target_column}" not found in dataset')
        
        # Preprocess data and create pipeline metadata
        X, y, feature_names, preprocessor = MLPreprocessor.preprocess_data(df, target_column, feature_columns)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        logger.info(f'Training set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples')
        
        # Select estimator
        if algorithm == 'randomforest':
            estimator = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif algorithm == 'linear':
            estimator = LinearRegression()
        else:
            raise ValueError(f'Unknown algorithm: {algorithm}')
        
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('estimator', estimator)
        ])
        
        # Train model pipeline
        start_time = datetime.utcnow()
        pipeline.fit(X_train, y_train)
        training_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Evaluate
        y_pred = pipeline.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))
        
        logger.info(f'Model Performance - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}')
        
        # Save full training pipeline
        file_name = f'{model_name.replace(" ", "_")}_{dataset_id}_{algorithm}.pkl'
        file_path = os.path.join(MODEL_DIR, file_name)
        joblib.dump(pipeline, file_path)
        
        # Create metadata
        meta = ModelMeta(
            user_id=user_id,
            dataset_id=dataset_id,
            name=model_name,
            model_type=model_type,
            algorithm=algorithm,
            rmse=rmse,
            accuracy=r2,  # Use R² for regression accuracy
            model_path=file_path,
            params={
                'features': feature_names,
                'target': target_column,
                'algorithm_params': {
                    'n_estimators': 100 if algorithm == 'randomforest' else None,
                    'max_depth': 20 if algorithm == 'randomforest' else None,
                }
            },
            feature_names=feature_names,
            target_column=target_column,
            training_samples=int(X_train.shape[0]),
            test_samples=int(X_test.shape[0]),
            training_time_seconds=training_time,
            status='trained',
            description=f'{algorithm} regression model for {target_column} prediction'
        )
        
        db.add(meta)
        db.commit()
        db.refresh(meta)
        logger.info(f'Model saved: {file_path}, ID: {meta.id}')
        
        return meta
    
    @staticmethod
    def train_classification_model(
        db: Session,
        dataset_id: int,
        target_column: str,
        feature_columns: Optional[list],
        model_name: str,
        model_type: str,
        user_id: int,
        algorithm: str = 'randomforest'
    ) -> ModelMeta:
        """Train classification model."""
        logger.info(f'Training {algorithm} classification model: {model_name}')
        
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError('Dataset not found')
        
        df = MLPipeline.load_dataset(dataset)
        if target_column not in df.columns:
            raise ValueError(f'Target column "{target_column}" not found in dataset')
        
        # Preprocess data and create pipeline metadata
        X, y, feature_names, preprocessor = MLPreprocessor.preprocess_data(df, target_column, feature_columns)
        
        # Encode labels if needed
        if y.dtype == 'object':
            le = LabelEncoder()
            y = le.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f'Training set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples')
        
        # Select estimator
        if algorithm == 'randomforest':
            estimator = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif algorithm == 'logistic':
            estimator = LogisticRegression(max_iter=1000, random_state=42)
        else:
            raise ValueError(f'Unknown algorithm: {algorithm}')
        
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('estimator', estimator)
        ])
        
        # Train model pipeline
        start_time = datetime.utcnow()
        pipeline.fit(X_train, y_train)
        training_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Evaluate
        y_pred = pipeline.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))
        precision = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
        recall = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
        
        logger.info(f'Model Performance - Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}')
        
        # Save full training pipeline
        file_name = f'{model_name.replace(" ", "_")}_{dataset_id}_{algorithm}.pkl'
        file_path = os.path.join(MODEL_DIR, file_name)
        joblib.dump(pipeline, file_path)
        
        # Create metadata
        meta = ModelMeta(
            user_id=user_id,
            dataset_id=dataset_id,
            name=model_name,
            model_type=model_type,
            algorithm=algorithm,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            model_path=file_path,
            params={
                'features': feature_names,
                'target': target_column,
                'algorithm_params': {
                    'n_estimators': 100 if algorithm == 'randomforest' else None,
                    'max_depth': 20 if algorithm == 'randomforest' else None,
                }
            },
            feature_names=feature_names,
            target_column=target_column,
            training_samples=int(X_train.shape[0]),
            test_samples=int(X_test.shape[0]),
            training_time_seconds=training_time,
            status='trained',
            description=f'{algorithm} classification model for {target_column} prediction'
        )
        
        db.add(meta)
        db.commit()
        db.refresh(meta)
        logger.info(f'Model saved: {file_path}, ID: {meta.id}')
        
        return meta

    @staticmethod
    def train_model(
        db: Session,
        dataset_id: int,
        target_column: str,
        feature_columns: Optional[list],
        model_name: str,
        model_type: str,
        user_id: int,
        algorithm: str = 'randomforest'
    ) -> ModelMeta:
        """Train the requested model type."""
        if model_type == 'regression':
            return MLPipeline.train_regression_model(
                db=db,
                dataset_id=dataset_id,
                target_column=target_column,
                feature_columns=feature_columns,
                model_name=model_name,
                model_type=model_type,
                user_id=user_id,
                algorithm=algorithm
            )
        elif model_type == 'classification':
            return MLPipeline.train_classification_model(
                db=db,
                dataset_id=dataset_id,
                target_column=target_column,
                feature_columns=feature_columns,
                model_name=model_name,
                model_type=model_type,
                user_id=user_id,
                algorithm=algorithm
            )
        else:
            raise ValueError(f'Unknown model_type: {model_type}')

    @staticmethod
    def predict(db: Session, model_id: int, record: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction with trained model."""
        model_meta = db.query(ModelMeta).filter(ModelMeta.id == model_id).first()
        if not model_meta:
            raise ValueError('Model not found')
        
        if not os.path.exists(model_meta.model_path):
            raise ValueError('Model file not found')
        
        # Load model
        model = joblib.load(model_meta.model_path)
        
        # Prepare raw feature data
        feature_names = model_meta.feature_names or model_meta.params.get('features', [])
        df_record = pd.DataFrame([record])

        for feature in feature_names:
            if feature not in df_record.columns:
                df_record[feature] = 0

        X = df_record[feature_names].fillna(0)

        prediction = model.predict(X)
        confidence = None
        
        if hasattr(model, 'predict_proba'):
            confidence = float(np.max(model.predict_proba(X)))
        
        return {
            'prediction': float(prediction[0]) if isinstance(prediction[0], (int, float, np.number)) else prediction[0],
            'confidence': confidence,
            'model_meta': model_meta
        }
    
    @staticmethod
    def get_model_status(db: Session, model_id: int) -> Dict[str, Any]:
        """Get model status and metrics."""
        model_meta = db.query(ModelMeta).filter(ModelMeta.id == model_id).first()
        if not model_meta:
            raise ValueError('Model not found')
        
        return {
            'id': model_meta.id,
            'name': model_meta.name,
            'model_type': model_meta.model_type,
            'algorithm': model_meta.algorithm,
            'status': model_meta.status,
            'accuracy': model_meta.accuracy,
            'precision': model_meta.precision,
            'recall': model_meta.recall,
            'f1_score': model_meta.f1_score,
            'rmse': model_meta.rmse,
            'training_samples': model_meta.training_samples,
            'test_samples': model_meta.test_samples,
            'training_time_seconds': model_meta.training_time_seconds,
            'created_at': model_meta.created_at,
            'description': model_meta.description
        }

MLTrainingService = MLPipeline
