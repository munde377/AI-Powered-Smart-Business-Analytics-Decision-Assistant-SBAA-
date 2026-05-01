"""Deep Learning pipeline for LSTM time-series forecasting."""
import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from ..models.model_meta import ModelMeta
from ..models.dataset import Dataset
from ..core.data_processor import DataProcessor

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage')
MODEL_DIR = os.path.join(DATA_DIR, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

class DLPipeline:
    """LSTM-based time-series forecasting pipeline."""

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
    def create_sequences(values: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training."""
        X, y = [], []
        for i in range(len(values) - lookback):
            X.append(values[i:i + lookback])
            y.append(values[i + lookback])
        return np.array(X), np.array(y)

    @staticmethod
    def build_lstm_model(lookback_steps: int) -> Sequential:
        """Build small LSTM model optimized for CPU."""
        model = Sequential([
            LSTM(32, activation='tanh', input_shape=(lookback_steps, 1), return_sequences=True),
            Dropout(0.2),
            LSTM(16, activation='tanh'),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        return model

    @staticmethod
    def train_lstm(
        db: Session,
        dataset_id: int,
        target_column: str,
        lookback_steps: int = 12,
        forecast_steps: int = 7,
        user_id: int = 0
    ) -> ModelMeta:
        """Train LSTM model for time-series forecasting."""
        logger.info(f'Training LSTM model for dataset {dataset_id}, target: {target_column}')

        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError('Dataset not found')

        df = DLPipeline.load_dataset(dataset)
        if target_column not in df.columns:
            raise ValueError(f'Target column "{target_column}" not found in dataset')

        # Extract and preprocess time series
        values = df[target_column].astype(float).fillna(method='ffill').fillna(0).values
        values = values.reshape(-1, 1)

        # Scale data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_values = scaler.fit_transform(values)

        # Create sequences
        X, y = DLPipeline.create_sequences(scaled_values, lookback_steps)

        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        logger.info(f'Training data: {X_train.shape[0]} sequences, Test data: {X_test.shape[0]} sequences')

        # Build and train model
        model = DLPipeline.build_lstm_model(lookback_steps)

        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=0
        )

        start_time = datetime.utcnow()
        history = model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=16,
            validation_data=(X_test, y_test),
            callbacks=[early_stopping],
            verbose=0
        )
        training_time = (datetime.utcnow() - start_time).total_seconds()

        # Evaluate
        loss, mae = model.evaluate(X_test, y_test, verbose=0)
        logger.info(f'LSTM Training completed - Loss: {loss:.4f}, MAE: {mae:.4f}')

        # Save model and scaler
        model_filename = f'lstm_forecast_{dataset_id}_{int(datetime.utcnow().timestamp())}.h5'
        scaler_filename = f'scaler_{dataset_id}_{int(datetime.utcnow().timestamp())}.pkl'

        model_path = os.path.join(MODEL_DIR, model_filename)
        scaler_path = os.path.join(MODEL_DIR, scaler_filename)

        model.save(model_path)

        # Save scaler
        import joblib
        joblib.dump(scaler, scaler_path)

        # Create metadata
        meta = ModelMeta(
            user_id=user_id,
            dataset_id=dataset_id,
            name=f'LSTM Forecast - {target_column}',
            model_type='lstm',
            algorithm='lstm',
            rmse=loss,  # Use loss as RMSE approximation
            accuracy=mae,  # Use MAE as accuracy metric
            model_path=model_path,
            params={
                'target_column': target_column,
                'lookback_steps': lookback_steps,
                'forecast_steps': forecast_steps,
                'scaler_path': scaler_path,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'epochs_trained': len(history.history['loss'])
            },
            feature_names=[target_column],
            target_column=target_column,
            training_samples=len(X_train),
            test_samples=len(X_test),
            training_time_seconds=training_time,
            status='trained',
            description=f'LSTM forecasting model for {target_column} with {lookback_steps} lookback steps'
        )

        db.add(meta)
        db.commit()
        db.refresh(meta)
        logger.info(f'LSTM model saved: {model_path}, ID: {meta.id}')

        return meta

    @staticmethod
    def predict_lstm(
        db: Session,
        model_id: int,
        history: List[float],
        forecast_steps: int = 7
    ) -> Dict[str, Any]:
        """Make LSTM predictions."""
        model_meta = db.query(ModelMeta).filter(ModelMeta.id == model_id).first()
        if not model_meta:
            raise ValueError('LSTM model not found')

        if not os.path.exists(model_meta.model_path):
            raise ValueError('LSTM model file not found')

        # Load model and scaler
        model = load_model(model_meta.model_path)
        import joblib
        scaler_path = model_meta.params.get('scaler_path')
        if not scaler_path or not os.path.exists(scaler_path):
            raise ValueError('Scaler not found')
        scaler = joblib.load(scaler_path)

        lookback_steps = model_meta.params.get('lookback_steps', 12)
        if len(history) < lookback_steps:
            raise ValueError(f'Need at least {lookback_steps} historical values')

        # Scale history
        history_scaled = scaler.transform(np.array(history).reshape(-1, 1))

        # Create input sequence
        sequence = history_scaled[-lookback_steps:].reshape(1, lookback_steps, 1)

        # Generate forecasts
        predictions = []
        for _ in range(forecast_steps):
            pred_scaled = model.predict(sequence, verbose=0)[0, 0]
            pred_original = scaler.inverse_transform([[pred_scaled]])[0, 0]
            predictions.append(float(pred_original))

            # Update sequence for next prediction
            sequence = np.roll(sequence, -1, axis=1)
            sequence[0, -1, 0] = pred_scaled

        logger.info(f'LSTM prediction completed for model {model_id}: {len(predictions)} steps')

        return {
            'predictions': predictions,
            'model_meta': model_meta,
            'forecast_steps': forecast_steps
        }

DLTrainingService = DLPipeline
