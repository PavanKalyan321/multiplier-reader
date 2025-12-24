"""
Analytics Client - Writes predictions to Supabase analytics_round_signals table
Handles all signal insertion and tracking
"""

import json
from datetime import datetime
from typing import Dict, Optional
from supabase import Client


class AnalyticsClient:
    """Handle analytics and prediction signal storage"""

    def __init__(self, supabase_client: Client):
        """
        Initialize analytics client

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        self.enabled = supabase_client is not None and hasattr(supabase_client, 'table')

    def insert_signal(self,
                     round_id: int,
                     round_number: int,
                     prediction: Dict,
                     volatility: float = 0.0,
                     momentum: float = 0.0,
                     bot_id: str = "multiplier-reader",
                     game_name: str = "aviator") -> bool:
        """
        Insert prediction signal into analytics_round_signals table

        Args:
            round_id: Unique round identifier
            round_number: Sequential round number
            prediction: Prediction dictionary from prediction_engine
            volatility: Volatility measure (0-1)
            momentum: Momentum score (-1 to 1)
            bot_id: Bot identifier
            game_name: Game name

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Extract signal information
            ensemble = prediction.get('ensemble', {})
            confidence = ensemble.get('confidence', 0.0)
            pred_value = ensemble.get('prediction', 0)

            # Determine signal type
            if confidence < 0.55:
                signal_type = "NEUTRAL"
            elif pred_value == 1 and confidence >= 0.75:
                signal_type = "STRONG_BULLISH"
            elif pred_value == 1 and confidence >= 0.55:
                signal_type = "BULLISH"
            elif pred_value == 0 and confidence >= 0.75:
                signal_type = "STRONG_BEARISH"
            else:
                signal_type = "BEARISH"

            # Calculate signal strength (confidence normalized)
            signal_strength = float(confidence)

            # Extract features
            features = prediction.get('features', {})

            # Prepare data for insertion
            data = {
                'round_id': round_id,
                'round_number': round_number,
                'timestamp': datetime.now().isoformat(),
                'bot_id': bot_id,
                'game_name': game_name,
                'signal_type': signal_type,
                'confidence_score': float(confidence),
                'signal_strength': signal_strength,
                'volatility_measure': float(volatility),
                'momentum_score': float(momentum),
                'pattern_match_type': self._get_pattern_type(features),
                'similar_rounds_count': self._estimate_similar_rounds(features),
                'feature_vector': json.dumps(features),
                'created_at': datetime.now().isoformat(),
            }

            # Insert into Supabase
            response = self.supabase.table('analytics_round_signals').insert(data).execute()

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Signal saved - {signal_type} (confidence: {confidence:.2f})")
            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to insert signal: {e}")
            return False

    def _get_pattern_type(self, features: Dict) -> str:
        """
        Determine pattern type from features

        Args:
            features: Feature dictionary

        Returns:
            Pattern type string
        """
        if not features:
            return "UNKNOWN"

        volatility = features.get('volatility', 0.5)
        crash_freq = features.get('crash_frequency', 0.5)
        trend = features.get('trend_5', 0.0)

        if volatility > 1.0:
            return "HIGH_VOLATILITY"
        elif crash_freq > 0.4:
            return "CRASH_PRONE"
        elif trend > 2.0:
            return "UPTREND"
        elif trend < -2.0:
            return "DOWNTREND"
        else:
            return "STABLE"

    def _estimate_similar_rounds(self, features: Dict) -> int:
        """
        Estimate number of similar rounds based on features

        Args:
            features: Feature dictionary

        Returns:
            Estimated count of similar rounds
        """
        if not features:
            return 0

        # Simple heuristic: estimate based on feature values
        win_rate = features.get('win_rate', 0.5)
        volatility = features.get('volatility', 0.5)

        # Higher win rate and lower volatility = more similar rounds
        similarity = (win_rate * 0.5) + ((1 - volatility) * 0.5)

        # Estimate: 5-50 similar rounds
        estimated = int(5 + (similarity * 45))
        return max(0, estimated)

    def update_signal_result(self,
                            signal_id: int,
                            actual_multiplier: float,
                            predicted_result: bool) -> bool:
        """
        Update signal with actual result after round completes

        Args:
            signal_id: Signal ID to update
            actual_multiplier: Actual crash multiplier
            predicted_result: Whether prediction was correct

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            # Calculate prediction error
            # (This assumes we had a target multiplier of 2.0 for bullish, <2.0 for bearish)
            prediction_error = actual_multiplier - 2.0

            data = {
                'actual_multiplier': float(actual_multiplier),
                'signal_correctness': bool(predicted_result),
                'prediction_error': float(prediction_error),
            }

            response = self.supabase.table('analytics_round_signals').update(data).eq('id', signal_id).execute()

            return True

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to update signal: {e}")
            return False

    def get_recent_signals(self, limit: int = 10, game_name: str = "aviator") -> list:
        """
        Get recent signals from database

        Args:
            limit: Number of recent signals to retrieve
            game_name: Filter by game name

        Returns:
            List of signal records
        """
        if not self.enabled:
            return []

        try:
            response = self.supabase.table('analytics_round_signals')\
                .select('*')\
                .eq('game_name', game_name)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()

            return response.data if hasattr(response, 'data') else []

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to retrieve signals: {e}")
            return []

    def get_signal_statistics(self, bot_id: str = "multiplier-reader") -> Dict:
        """
        Get statistics about recent signals

        Args:
            bot_id: Filter by bot ID

        Returns:
            Dictionary with signal statistics
        """
        if not self.enabled:
            return {}

        try:
            response = self.supabase.table('analytics_round_signals')\
                .select('signal_type, confidence_score, signal_correctness')\
                .eq('bot_id', bot_id)\
                .order('timestamp', desc=True)\
                .limit(100)\
                .execute()

            signals = response.data if hasattr(response, 'data') else []

            if not signals:
                return {'total': 0}

            stats = {
                'total': len(signals),
                'by_signal_type': {},
                'avg_confidence': 0.0,
                'accuracy': 0.0,
            }

            # Count by signal type
            for signal in signals:
                signal_type = signal.get('signal_type', 'UNKNOWN')
                stats['by_signal_type'][signal_type] = stats['by_signal_type'].get(signal_type, 0) + 1

            # Average confidence
            confidences = [float(s.get('confidence_score', 0)) for s in signals]
            stats['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0

            # Accuracy (where correctness is recorded)
            correct_signals = [s for s in signals if s.get('signal_correctness') is not None]
            if correct_signals:
                correct_count = sum(1 for s in correct_signals if s.get('signal_correctness') is True)
                stats['accuracy'] = correct_count / len(correct_signals)

            return stats

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Failed to get signal statistics: {e}")
            return {}
