"""
Prediction Orchestrator
Coordinates 15 AutoML models and aggregates predictions
"""

import numpy as np
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from strategy_engine import StrategyEngine


class MockModel:
    """Mock model for demonstration - will be replaced with actual models"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.confidence_base = 0.65 + (hash(model_name) % 20) / 100  # 0.65-0.85

    def predict(self, historical_data: List[Dict]) -> Dict:
        """Generate mock prediction"""
        multipliers = [r['multiplier'] for r in historical_data]
        avg_mult = np.mean(multipliers)

        # Add some variance based on model
        variance = (hash(self.model_name) % 30) / 100
        predicted = avg_mult + variance

        return {
            'predicted_multiplier': max(1.0, predicted),
            'confidence': min(0.95, self.confidence_base + np.random.uniform(-0.05, 0.05)),
            'min': max(1.0, predicted * 0.8),
            'max': predicted * 1.2
        }


class PredictionOrchestrator:
    """Orchestrates 15 AutoML models for predictions"""

    def __init__(self):
        """Initialize and load all 15 AutoML models"""
        self.strategy_engine = StrategyEngine()

        # Initialize models (currently using mock models for demonstration)
        # In production, these would be actual trained ML models
        self.models = {
            'PyCaret': MockModel('PyCaret'),
            'H2O_AutoML': MockModel('H2O_AutoML'),
            'AutoSklearn': MockModel('AutoSklearn'),
            'LSTM_Model': MockModel('LSTM_Model'),
            'AutoGluon': MockModel('AutoGluon'),
            'RandomForest_AutoML': MockModel('RandomForest_AutoML'),
            'CatBoost': MockModel('CatBoost'),
            'LightGBM_AutoML': MockModel('LightGBM_AutoML'),
            'XGBoost_AutoML': MockModel('XGBoost_AutoML'),
            'MLP_NeuralNet': MockModel('MLP_NeuralNet'),
            'TPOT_Genetic': MockModel('TPOT_Genetic'),
            'AutoKeras': MockModel('AutoKeras'),
            'AutoPyTorch': MockModel('AutoPyTorch'),
            'MLBox': MockModel('MLBox'),
            'TransmogrifAI': MockModel('TransmogrifAI')
        }

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Loaded {len(self.models)} AutoML models")

    def get_model_count(self) -> int:
        """Get total number of loaded models"""
        return len(self.models)

    def predict_all_models(self, historical_data: List[Dict]) -> List[Dict]:
        """
        Run all 15 models in parallel and aggregate predictions

        Args:
            historical_data: List of historical round data

        Returns:
            List of 15 model predictions
        """
        if not historical_data:
            return []

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Running 15 models on {len(historical_data)} historical rounds...")

        # Extract multipliers for pattern detection
        multipliers = [r['multiplier'] for r in historical_data]
        pattern = self.strategy_engine.detect_pattern(multipliers)

        print(f"[{timestamp}] INFO: Detected pattern: {pattern}")

        # Run models in parallel
        predictions = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_model = {
                executor.submit(self._run_single_model, model_name, model, historical_data, pattern):
                model_name for model_name, model in self.models.items()
            }

            for future in as_completed(future_to_model):
                try:
                    pred = future.result()
                    if pred:
                        predictions.append(pred)
                except Exception as e:
                    model_name = future_to_model[future]
                    print(f"[{timestamp}] WARNING: Model {model_name} failed: {e}")

        # Sort by model name for consistency
        predictions.sort(key=lambda x: x['model_name'])

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: All {len(predictions)} models executed successfully")

        return predictions

    def _run_single_model(self, model_name: str, model, historical_data: List[Dict],
                         pattern: str) -> Dict:
        """
        Run a single model and return prediction

        Args:
            model_name: Name of the model
            model: Model instance
            historical_data: Historical data for prediction
            pattern: Detected pattern from strategy engine

        Returns:
            Prediction dict with model outputs
        """
        try:
            # Generate raw prediction
            raw_pred = model.predict(historical_data)

            # Get strategy parameters
            strategy = self.strategy_engine.get_strategy_for_model(
                model_name, pattern, raw_pred['predicted_multiplier']
            )

            # Build prediction object
            prediction = {
                'model_name': model_name,
                'predicted_multiplier': round(raw_pred['predicted_multiplier'], 1),
                'confidence': round(raw_pred['confidence'], 2),
                'range': [round(raw_pred['min'], 1), round(raw_pred['max'], 1)],
                'strategy': strategy['strategy'],
                'bet': raw_pred['confidence'] >= strategy['bet_threshold'],
                'timestamp': datetime.now().isoformat()
            }

            return prediction

        except Exception as e:
            print(f"ERROR: Model {model_name} execution failed: {e}")
            return None
