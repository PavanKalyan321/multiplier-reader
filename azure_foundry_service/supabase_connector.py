"""
Supabase Connector
Handles all database operations for Azure AI Foundry service
"""

import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from supabase import create_client, Client


class SupabaseConnector:
    """Manages Supabase database connection and operations"""

    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.client: Client = None
        self.enabled = False

        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                self.enabled = True
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] INFO: Supabase connected successfully")
            except Exception as e:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] WARNING: Supabase connection failed: {e}")
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Supabase credentials not provided")

    def is_connected(self) -> bool:
        """Check if Supabase is connected"""
        return self.enabled

    def fetch_last_24h(self) -> List[Dict]:
        """
        Fetch rounds from last 24 hours from AviatorRound table

        Returns:
            List of round data dictionaries
        """
        if not self.enabled:
            return []

        try:
            # Calculate 24 hours ago
            cutoff_time = datetime.now() - timedelta(hours=24)
            cutoff_iso = cutoff_time.isoformat()

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Fetching rounds from last 24 hours...")

            # Query AviatorRound table
            response = self.client.table('AviatorRound') \
                .select('roundId, multiplier, timestamp') \
                .gte('timestamp', cutoff_iso) \
                .order('timestamp', desc=False) \
                .execute()

            rounds = response.data if response.data else []

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Retrieved {len(rounds)} rounds from last 24 hours")

            return rounds

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to fetch historical data: {e}")
            return []

    def insert_analytics_signal(self, round_id: int, round_number: int,
                               payload: Dict) -> Optional[int]:
        """
        Insert prediction signal to analytics_round_signals table

        Args:
            round_id: Unique round identifier
            round_number: Sequential round number
            payload: Full modelPredictions payload with 15 models

        Returns:
            Signal ID if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Extract automl predictions
            automl_predictions = payload.get('modelPredictions', {}).get('automl', [])

            if not automl_predictions:
                print(f"[{timestamp}] WARNING: No predictions in payload")
                return None

            # Calculate ensemble metrics
            confidences = [p.get('confidence', 0) for p in automl_predictions]
            ensemble_confidence = sum(confidences) / len(confidences) if confidences else 0.5

            predictions_vals = [p.get('predicted_multiplier', 0) for p in automl_predictions]
            avg_prediction = sum(predictions_vals) / len(predictions_vals) if predictions_vals else 1.5

            # Determine signal type
            signal_type = self._calculate_signal_type(avg_prediction, ensemble_confidence)

            # Prepare data for insertion
            data = {
                'round_id': round_id,
                'round_number': round_number,
                'timestamp': datetime.now().isoformat(),
                'bot_id': 'azure-foundry',
                'game_name': 'aviator',
                'signal_type': signal_type,
                'confidence_score': float(ensemble_confidence),
                'signal_strength': float(ensemble_confidence),
                'volatility_measure': self._calculate_volatility(predictions_vals),
                'momentum_score': self._calculate_momentum(predictions_vals),
                'pattern_match_type': self._detect_pattern_type(automl_predictions),
                'similar_rounds_count': 24,  # Based on 24h window
                'feature_vector': json.dumps({}),  # Can be extended with features
                'payload': json.dumps(payload),  # Full 15-model payload
                'created_at': datetime.now().isoformat()
            }

            # Insert into database
            response = self.client.table('analytics_round_signals').insert(data).execute()

            if response.data and len(response.data) > 0:
                signal_id = response.data[0].get('id')
                print(f"[{timestamp}] INFO: Signal inserted (ID: {signal_id}, Type: {signal_type}, Confidence: {ensemble_confidence:.2%})")
                return signal_id
            else:
                print(f"[{timestamp}] WARNING: Signal inserted but no ID returned")
                return None

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ERROR: Failed to insert analytics signal: {e}")
            return None

    def _calculate_signal_type(self, avg_prediction: float, ensemble_confidence: float) -> str:
        """Determine signal type from ensemble prediction and confidence"""
        if ensemble_confidence < 0.55:
            return "NEUTRAL"
        elif avg_prediction >= 2.5 and ensemble_confidence >= 0.75:
            return "STRONG_BULLISH"
        elif avg_prediction >= 2.0 and ensemble_confidence >= 0.60:
            return "BULLISH"
        elif avg_prediction < 1.5 and ensemble_confidence >= 0.75:
            return "STRONG_BEARISH"
        elif avg_prediction < 1.8:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_volatility(self, predictions: List[float]) -> float:
        """Calculate volatility measure from predictions"""
        if len(predictions) < 2:
            return 0.0
        return float(np.std(predictions) if predictions else 0.0)

    def _calculate_momentum(self, predictions: List[float]) -> float:
        """Calculate momentum score from predictions"""
        if len(predictions) < 2:
            return 0.0

        avg = np.mean(predictions) if predictions else 1.5
        recent = np.mean(predictions[-5:]) if len(predictions) >= 5 else avg

        # Momentum: how much recent predictions exceed average
        momentum = (recent - avg) / avg if avg > 0 else 0.0
        return float(momentum)

    def _detect_pattern_type(self, predictions: List[Dict]) -> str:
        """Detect pattern type from model predictions"""
        if not predictions:
            return "UNKNOWN"

        # Count bullish vs bearish predictions
        bullish = sum(1 for p in predictions if p.get('predicted_multiplier', 0) >= 2.0)
        bearish = sum(1 for p in predictions if p.get('predicted_multiplier', 0) < 1.5)
        total = len(predictions)

        bullish_ratio = bullish / total if total > 0 else 0.5
        bearish_ratio = bearish / total if total > 0 else 0.5

        if bullish_ratio >= 0.6:
            return "HIGH_VOLATILITY"
        elif bearish_ratio >= 0.6:
            return "CRASH_PRONE"
        else:
            return "STABLE"

    def get_round_by_id(self, round_id: int) -> Optional[Dict]:
        """
        Fetch a specific round by ID

        Args:
            round_id: Round ID to fetch

        Returns:
            Round data dict or None
        """
        if not self.enabled:
            return None

        try:
            response = self.client.table('AviatorRound') \
                .select('*') \
                .eq('roundId', round_id) \
                .single() \
                .execute()

            return response.data

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to fetch round {round_id}: {e}")
            return None

    def get_signal_by_id(self, signal_id: int) -> Optional[Dict]:
        """
        Fetch a specific signal by ID

        Args:
            signal_id: Signal ID to fetch

        Returns:
            Signal data dict or None
        """
        if not self.enabled:
            return None

        try:
            response = self.client.table('analytics_round_signals') \
                .select('*') \
                .eq('id', signal_id) \
                .single() \
                .execute()

            return response.data

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to fetch signal {signal_id}: {e}")
            return None
