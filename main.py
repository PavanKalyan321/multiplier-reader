# Main monitoring loop for multiplier reader
import time
import sys
import json
import os
from datetime import datetime
from config import load_config, get_default_region
from screen_capture import ScreenCapture
from multiplier_reader import MultiplierReader
from game_tracker import GameTracker
from supabase_client import SupabaseLogger
from auto_refresh import AutoRefresher
from azure_foundry_client import AzureFoundryClient
# Try importing advanced ML system first, then fall back to multi-model, then single model
try:
    from ml_system.prediction_engine import PredictionEngine
    from ml_system.config import MLSystemConfig
    ADVANCED_ML_AVAILABLE = True
    ML_AVAILABLE = True
except ImportError:
    ADVANCED_ML_AVAILABLE = False
    try:
        from multi_model_predictor import MultiModelPredictor, ML_AVAILABLE
        MULTI_MODEL_AVAILABLE = True
    except ImportError:
        MULTI_MODEL_AVAILABLE = False
        from ml_predictor import CrashPredictor, ML_AVAILABLE


class Colors:
    """ANSI color codes for terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Status colors
    GREEN = '\033[92m'   # Low multiplier (1x-3x)
    YELLOW = '\033[93m'  # Medium (3x-7x)
    RED = '\033[91m'     # High (7x-10x)
    MAGENTA = '\033[95m' # Very high (10x+)

    # Info colors
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'

    @staticmethod
    def get_multiplier_color(mult):
        """Get color based on multiplier value"""
        if mult >= 10:
            return Colors.MAGENTA
        elif mult >= 7:
            return Colors.RED
        elif mult >= 3:
            return Colors.YELLOW
        else:
            return Colors.GREEN


class MultiplierReaderApp:
    """Main application for monitoring game multiplier"""

    def __init__(self, region=None, update_interval=0.5, auto_refresh_interval=900):
        self.region = region or load_config() or get_default_region()
        self.update_interval = update_interval
        self.screen_capture = ScreenCapture(self.region)
        self.multiplier_reader = MultiplierReader(self.screen_capture)
        self.game_tracker = GameTracker()
        self.running = False
        self.previous_round_count = 0
        self.is_round_running = False
        self.last_status_msg = ""
        self.status_printed = False
        self.multiplier_history = []  # Track last N multipliers for sparkline
        self.max_history = 10  # Keep last 10 values

        # Initialize auto-refresher (15 minutes by default)
        self.auto_refresher = AutoRefresher(self.region, refresh_interval=auto_refresh_interval)

        # Initialize Supabase logger
        self.supabase = SupabaseLogger(
            url='https://zofojiubrykbtmstfhzx.supabase.co',
            key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
        )

        # Initialize Azure AI Foundry client
        self.azure_foundry_client = AzureFoundryClient(
            endpoint_url=os.getenv('AZURE_FOUNDRY_ENDPOINT'),
            api_key=os.getenv('AZURE_FOUNDRY_API_KEY')
        )

        # Initialize ML predictor (try advanced ML first, then fallback)
        self.predictor = None
        self.current_prediction_ids = {}  # Track prediction IDs per model
        self.use_multi_model = False
        self.use_advanced_ml = False

        if ML_AVAILABLE:
            if ADVANCED_ML_AVAILABLE:
                # Use advanced ML system (25+ models, hybrid strategy, patterns)
                self.predictor = PredictionEngine(history_size=1000, min_rounds_for_prediction=5)
                self.use_advanced_ml = True
                self.use_multi_model = True  # Also enable multi-model flag for compatibility
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Advanced ML System initialized (25+ models)")
            elif MULTI_MODEL_AVAILABLE:
                self.predictor = MultiModelPredictor(history_size=1000, min_rounds_for_prediction=5)
                self.use_multi_model = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Multi-Model Predictor initialized (5 models)")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Models: RandomForest, GradientBoosting, Ridge, Lasso, DecisionTree")
            else:
                self.predictor = CrashPredictor(history_size=1000, min_rounds_for_prediction=5)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Single ML Predictor initialized (RandomForest only)")

            # Try to load historical data from Supabase
            self._load_historical_data()
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: ML libraries not installed. Run: pip install scikit-learn")

        self.stats = {
            'total_updates': 0,
            'successful_reads': 0,
            'failed_reads': 0,
            'crashes_detected': 0,
            'max_multiplier_ever': 0,
            'azure_predictions': 0,      # Track Azure Foundry predictions
            'azure_failures': 0,         # Track Azure Foundry failures
            'signals_saved': 0,          # Track saved signals
            'start_time': datetime.now(),
            'supabase_inserts': 0,      # Track successful inserts
            'supabase_failures': 0,      # Track failed inserts
            'predictions_made': 0,       # Track ML predictions
            'prediction_errors': [],     # Track prediction accuracy
        }

    def _load_historical_data(self):
        """Load historical round data from Supabase to initialize ML model"""
        if not self.predictor or not self.supabase.enabled:
            return

        try:
            # Fetch ALL available rounds from Supabase (no limit)
            rounds = self.supabase.get_recent_rounds(limit=None)

            if not rounds:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: No historical data in Supabase, will collect from scratch")
                return

            # Add rounds to predictor (in chronological order, oldest first)
            rounds_reverse = list(reversed(rounds))  # Reverse since query returns newest first

            for round_data in rounds_reverse:
                multiplier = round_data.get('multiplier')
                timestamp_str = round_data.get('timestamp')

                if multiplier and timestamp_str:
                    # Parse timestamp
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str).timestamp()
                    except:
                        timestamp = time.time()

                    # Estimate duration (we don't have this in DB, use average ~3 seconds)
                    duration = 3.0

                    self.predictor.add_round(
                        crash_multiplier=multiplier,
                        duration=duration,
                        timestamp=timestamp
                    )

            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Loaded {len(rounds)} historical rounds for ML training")

            # Train the model if we have enough data
            if len(rounds) >= self.predictor.min_rounds_for_prediction:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Training ML model...")
                self.predictor.train(lookback=10)

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to load historical data: {e}")

    def generate_sparkline(self, values, width=10):
        """Generate ASCII sparkline from values"""
        if not values or len(values) < 2:
            return ' ' * min(width, len(values) if values else 1)

        # Normalize values to 0-7 range for block chars
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            return '-' * min(len(values), width)

        # Use ASCII characters that work in most terminals
        blocks = ['_', '.', '-', '=', '^', '*', '#', '@']

        result = []
        for val in values[-width:]:
            normalized = int(((val - min_val) / (max_val - min_val)) * 7)
            result.append(blocks[normalized])

        return ''.join(result)

    def log_event(self, event):
        """Log events with color coding"""
        if event.event_type == 'CRASH':
            max_mult = event.details.get('max_multiplier', 'N/A')
            duration = event.details.get('round_duration', 0)
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Print newline first to move to new line after status, then clear line
            print(f"\n{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.RED}{Colors.BOLD}[CRASH]{Colors.RESET} Reached {Colors.MAGENTA}{max_mult}x{Colors.RESET} in {duration:.2f}s")
            self.stats['crashes_detected'] += 1
        elif event.event_type == 'GAME_START':
            timestamp = datetime.now().strftime("%H:%M:%S")
            round_num = self.game_tracker.round_number + 1
            # Print newline first to move to new line after status
            print(f"\n{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.GREEN}{Colors.BOLD}[START]{Colors.RESET} ROUND {round_num} STARTED")
            self.is_round_running = True
            self.multiplier_history = []  # Reset sparkline on new round
        elif event.event_type == 'HIGH_MULTIPLIER':
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.MAGENTA}{Colors.BOLD}[HIGH]{Colors.RESET} MULTIPLIER: {Colors.MAGENTA}{event.multiplier:.2f}x{Colors.RESET}")
        # NOTE: MULTIPLIER_INCREASE events are NOT logged to avoid clutter - shown only in status line

    def check_and_log_round_completion(self):
        """Check if a new round was completed and log it"""
        current_round_count = len(self.game_tracker.round_history)
        if current_round_count > self.previous_round_count:
            # A new round was just completed
            new_round = self.game_tracker.round_history[-1]
            self.log_round_completion(new_round)
            self.previous_round_count = current_round_count
            self.is_round_running = False

    def log_round_completion(self, round_summary):
        """Log a completed round with formatted table and save to Supabase"""
        print("\n")
        print("=" * 80)
        print("ROUND ENDED")
        print("=" * 80)
        print()

        # Log the complete round history table - DISABLED
        # history_table = self.game_tracker.format_round_history_table(limit=None)
        # print(history_table)

        # Step 1: Insert round data into Supabase (AviatorRound table)
        round_end_time = datetime.fromtimestamp(round_summary.end_time)
        round_id = self.supabase.insert_round(
            round_number=round_summary.round_number,
            multiplier=round_summary.max_multiplier,
            timestamp=round_end_time
        )

        # Update stats
        if round_id:
            self.stats['supabase_inserts'] += 1
        else:
            self.stats['supabase_failures'] += 1
            round_id = None  # Make sure it's None for later checks

        # Call Azure AI Foundry for prediction (if round was saved)
        if round_id and self.azure_foundry_client.enabled:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] INFO: Requesting prediction from Azure AI Foundry...")

                result = self.azure_foundry_client.request_prediction(
                    round_id=round_id,
                    round_number=round_summary.round_number
                )

                if result.get('status') == 'success':
                    self.stats['azure_predictions'] += 1
                    self.stats['signals_saved'] += 1
                    print(f"[{timestamp}] SUCCESS: Azure AI Foundry prediction completed")
                    print(f"[{timestamp}]   - Models executed: {result.get('models_executed', 0)}")
                    print(f"[{timestamp}]   - Ensemble confidence: {result.get('ensemble_confidence', 0):.1%}")
                else:
                    self.stats['azure_failures'] += 1
                    print(f"[{timestamp}] WARNING: Azure prediction failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                self.stats['azure_failures'] += 1
                print(f"[{timestamp}] WARNING: Azure AI Foundry error: {e}")

        # Update ML predictor with actual result (if we had a prediction)
        if self.predictor and len(self.current_prediction_ids) > 0:
            # Update predictor's internal accuracy tracking
            self.predictor.update_prediction_accuracy(round_summary.max_multiplier)

            # Calculate error for stats
            if self.use_multi_model and hasattr(self.predictor, 'last_predictions') and self.predictor.last_predictions:
                # Use ensemble prediction for error calculation (multi-model)
                for model_name, pred in self.predictor.last_predictions.items():
                    error = abs(pred['predicted_multiplier'] - round_summary.max_multiplier)
                    if 'prediction_errors' not in self.stats:
                        self.stats['prediction_errors'] = []
                    self.stats['prediction_errors'].append(error)
            elif hasattr(self.predictor, 'last_prediction') and self.predictor.last_prediction:
                # Single model prediction
                error = abs(self.predictor.last_prediction['predicted_multiplier'] - round_summary.max_multiplier)
                if 'prediction_errors' not in self.stats:
                    self.stats['prediction_errors'] = []
                self.stats['prediction_errors'].append(error)

        # Add this round to ML predictor history
        if self.predictor:
            self.predictor.add_round(
                crash_multiplier=round_summary.max_multiplier,
                duration=round_summary.duration,
                timestamp=round_summary.end_time
            )

            # Retrain the model periodically (every 10 rounds)
            if round_summary.round_number % 10 == 0 and self.predictor.is_trained:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Retraining ML model with new data...")
                self.predictor.train(lookback=5)

        # Step 2: Make prediction for NEXT round and save to analytics table
        if round_id:  # Only make prediction if round was saved successfully
            self._make_prediction_for_next_round(
                round_summary.round_number + 1,
                last_round_id=round_id,
                last_round_multiplier=round_summary.max_multiplier,
                round_timestamp=round_end_time
            )

        print()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Waiting for next round...")

    def _make_prediction_for_next_round(self, next_round_number, last_round_id=None,
                                        last_round_multiplier=None, round_timestamp=None):
        """Make ML prediction for the next round and save to analytics table"""
        if not self.predictor:
            return

        # Check if we have enough data to make predictions
        if len(self.predictor.round_history) < self.predictor.min_rounds_for_prediction:
            remaining = self.predictor.min_rounds_for_prediction - len(self.predictor.round_history)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Need {remaining} more rounds before ML predictions can start")
            return

        # Train if not yet trained
        if not self.predictor.is_trained:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Training ML model for first time...")
            # Use adaptive lookback based on available rounds
            lookback = min(5, len(self.predictor.round_history))
            if self.predictor.train(lookback=lookback):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Model trained successfully!")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Model training failed")
                return

        # Make prediction (use adaptive lookback)
        lookback = min(5, len(self.predictor.round_history))

        # Get predictions (advanced ML, multi-model, or single)
        if self.use_advanced_ml:
            # Advanced ML system (25+ models, hybrid strategy, patterns)
            result = self.predictor.predict_all(lookback=lookback)
            if not result:
                return

            ensemble = result['ensemble']
            hybrid = result['hybrid_strategy']
            all_predictions = result['all_predictions']
            patterns = result['patterns']

            # Display advanced predictions
            self._display_advanced_predictions(next_round_number, ensemble, hybrid, all_predictions, patterns)

        elif self.use_multi_model:
            predictions = self.predictor.predict_all(lookback=lookback)
            if not predictions:
                return

            # Get ensemble prediction
            ensemble = self.predictor.get_ensemble_prediction(predictions)

            # Display all model predictions
            print()
            print("=" * 80)
            print(f"{Colors.CYAN}{Colors.BOLD}ML PREDICTIONS FOR ROUND {next_round_number} (Multi-Model){Colors.RESET}")
            print("=" * 80)

            # Show ensemble first
            print(f"\n{Colors.BOLD}{Colors.YELLOW}ENSEMBLE PREDICTION:{Colors.RESET}")
            print(f"  Multiplier: {Colors.get_multiplier_color(ensemble['predicted_multiplier'])}{ensemble['predicted_multiplier']:.2f}x{Colors.RESET}")
            print(f"  Confidence: {ensemble['confidence'] * 100:.0f}%")
            print(f"  Range: {ensemble['range'][0]:.2f}x - {ensemble['range'][1]:.2f}x")
            print(f"  Bet: {Colors.GREEN if ensemble['bet'] else Colors.RED}{'YES' if ensemble['bet'] else 'NO'}{Colors.RESET}")
            if 'bet_votes' in ensemble:
                print(f"  Bet Votes: {ensemble['bet_votes']}")

            # Show individual model predictions
            print(f"\n{Colors.BOLD}Individual Models:{Colors.RESET}")
            for pred in predictions:
                bet_indicator = f"{Colors.GREEN}✓{Colors.RESET}" if pred['bet'] else f"{Colors.RED}✗{Colors.RESET}"
                print(f"  {pred['model_name']:20s} {pred['predicted_multiplier']:5.2f}x  Conf: {pred['confidence']*100:3.0f}%  Bet: {bet_indicator}")

            # Show statistics
            predictor_stats = self.predictor.get_statistics()
            print(f"\n{Colors.BOLD}Statistics:{Colors.RESET}")
            print(f"  Total Predictions: {predictor_stats['predictions_made']}")
            print(f"  Rounds Collected: {predictor_stats['rounds_collected']}")

            print("=" * 80)
            print()

        else:
            # Single model prediction (legacy)
            prediction = self.predictor.predict(lookback=lookback)
            if not prediction:
                return

            predicted_mult = prediction['predicted_multiplier']
            confidence = prediction['confidence']

            print()
            print("=" * 80)
            print(f"{Colors.CYAN}{Colors.BOLD}ML PREDICTION FOR ROUND {next_round_number}{Colors.RESET}")
            print("=" * 80)
            print(f"{Colors.BOLD}Predicted Crash Multiplier:{Colors.RESET} {Colors.get_multiplier_color(predicted_mult)}{predicted_mult:.2f}x{Colors.RESET}")
            print(f"{Colors.BOLD}Confidence:{Colors.RESET} {confidence * 100:.1f}%")
            print(f"{Colors.BOLD}Model:{Colors.RESET} {prediction['model_type']}")
            print(f"{Colors.BOLD}Training Samples:{Colors.RESET} {prediction['training_samples']}")

            # Show prediction accuracy statistics if available
            predictor_stats = self.predictor.get_statistics()
            if predictor_stats['predictions_made'] > 0:
                print(f"{Colors.BOLD}Predictions Made:{Colors.RESET} {predictor_stats['predictions_made']}")
                print(f"{Colors.BOLD}Average Error:{Colors.RESET} {predictor_stats['avg_error']:.2f}x")

            print("=" * 80)
            print()

        # Save predictions to database
        if last_round_id and last_round_multiplier is not None:
            if self.use_advanced_ml:
                # Save advanced multi-model predictions (25+ models, hybrid, patterns)
                signal_id = self.supabase.insert_advanced_multi_model_signal(
                    round_id=last_round_id,
                    actual_multiplier=last_round_multiplier,
                    ensemble_prediction=ensemble,
                    hybrid_decision=hybrid,
                    all_predictions=all_predictions,
                    patterns=patterns,
                    timestamp=round_timestamp
                )

                if signal_id:
                    self.current_prediction_ids['advanced_multi_model'] = signal_id

            elif self.use_multi_model:
                # Save multi-model predictions (includes ensemble + all individual models)
                all_predictions_list = [ensemble] + predictions

                signal_id = self.supabase.insert_multi_model_signal(
                    round_id=last_round_id,
                    actual_multiplier=last_round_multiplier,
                    predictions=all_predictions_list,
                    timestamp=round_timestamp
                )

                if signal_id:
                    self.current_prediction_ids['multi_model'] = signal_id

            else:
                # Save single model prediction (legacy)
                range_margin = predicted_mult * 0.2
                prediction_range = (
                    max(1.0, predicted_mult - range_margin),
                    predicted_mult + range_margin
                )

                model_output = {
                    'predicted_multiplier': predicted_mult,
                    'prediction_timestamp': prediction.get('timestamp'),
                    'prediction_number': prediction.get('prediction_number'),
                    'features_used': 21
                }

                metadata = {
                    'next_round_number': next_round_number,
                    'predictor_stats': predictor_stats
                }

                signal_id = self.supabase.insert_analytics_signal(
                    round_id=last_round_id,
                    actual_multiplier=last_round_multiplier,
                    predicted_multiplier=predicted_mult,
                    model_name=prediction.get('model_type', 'RandomForest'),
                    confidence=confidence,
                    prediction_range=prediction_range,
                    model_output=model_output,
                    metadata=metadata,
                    timestamp=round_timestamp
                )

                if signal_id:
                    self.current_prediction_ids['single'] = signal_id

        self.stats['predictions_made'] += 1

    def _display_advanced_predictions(self, round_num, ensemble, hybrid, all_predictions, patterns):
        """Display advanced multi-model predictions with hybrid strategy and patterns"""
        import numpy as np

        print()
        print("=" * 130)
        print(f"{Colors.CYAN}{Colors.BOLD}ML PREDICTIONS FOR ROUND {round_num} (Advanced Multi-Model System - 16 AutoML Models){Colors.RESET}")
        print("=" * 130)

        # Display detailed table of ALL model predictions - DISABLED
        # print(f"\n{Colors.BOLD}ALL MODEL PREDICTIONS - DETAILED VIEW{Colors.RESET}")
        # print("-" * 130)
        # print(f"{'Model Name':<30} {'Prediction':<12} {'Confidence':<12} {'Range':<22} {'Bet':<8}")
        # print("-" * 130)

        # Legacy Models - DISABLED
        # if all_predictions.get('legacy'):
        #     print(f"\n{Colors.YELLOW}[LEGACY MODELS]{Colors.RESET}")
        #     for model in all_predictions['legacy']:
        #         name = model.get('model_name', 'Unknown')
        #         pred = model.get('predicted_multiplier', 0)
        #         conf = model.get('confidence', 0) * 100
        #         range_min, range_max = model.get('range', (0, 0))
        #         bet = model.get('bet', False)
        #         bet_color = Colors.GREEN if bet else Colors.RED
        #         bet_str = f"{bet_color}{'YES' if bet else 'NO'}{Colors.RESET}"
        #         pred_color = Colors.get_multiplier_color(pred)
        #         print(f"{name:<30} {pred_color}{pred:>6.2f}x{Colors.RESET}      {conf:>5.0f}%        {range_min:>5.2f}x - {range_max:<6.2f}x   {bet_str}")

        # AutoML Models - DISABLED
        # if all_predictions.get('automl'):
        #     print(f"\n{Colors.YELLOW}[AUTOML MODELS]{Colors.RESET}")
        #     for model in all_predictions['automl']:
        #         name = model.get('model_name', 'Unknown')
        #         pred = model.get('predicted_multiplier', 0)
        #         conf = model.get('confidence', 0) * 100
        #         range_min, range_max = model.get('range', (0, 0))
        #         bet = model.get('bet', False)
        #         bet_color = Colors.GREEN if bet else Colors.RED
        #         bet_str = f"{bet_color}{'YES' if bet else 'NO'}{Colors.RESET}"
        #         pred_color = Colors.get_multiplier_color(pred)
        #         print(f"{name:<30} {pred_color}{pred:>6.2f}x{Colors.RESET}      {conf:>5.0f}%        {range_min:>5.2f}x - {range_max:<6.2f}x   {bet_str}")

        # Trained Models - DISABLED
        # if all_predictions.get('trained'):
        #     print(f"\n{Colors.YELLOW}[TRAINED MODELS]{Colors.RESET}")
        #     for model in all_predictions['trained']:
        #         name = model.get('model_name', 'Unknown')
        #         pred = model.get('predicted_multiplier', 0)
        #         conf = model.get('confidence', 0) * 100
        #         range_min, range_max = model.get('range', (0, 0))
        #         bet = model.get('bet', False)
        #         bet_color = Colors.GREEN if bet else Colors.RED
        #         bet_str = f"{bet_color}{'YES' if bet else 'NO'}{Colors.RESET}"
        #         pred_color = Colors.get_multiplier_color(pred)
        #         print(f"{name:<30} {pred_color}{pred:>6.2f}x{Colors.RESET}      {conf:>5.0f}%        {range_min:>5.2f}x - {range_max:<6.2f}x   {bet_str}")

        # Binary Classifiers - DISABLED
        # if all_predictions.get('classifiers'):
        #     print(f"\n{Colors.YELLOW}[BINARY CLASSIFIERS]{Colors.RESET}")
        #     for model in all_predictions['classifiers']:
        #         name = model.get('model_name', 'Unknown')
        #         target = model.get('target', 0)
        #         prob = model.get('probability', model.get('confidence', 0)) * 100
        #         bet = model.get('bet', False)
        #         bet_color = Colors.GREEN if bet else Colors.RED
        #         bet_str = f"{bet_color}{'YES' if bet else 'NO'}{Colors.RESET}"
        #         print(f"{name:<30} Target:{target:.1f}x   Prob: {prob:>5.0f}%        N/A                    {bet_str}")

        # print("-" * 130)

        # Ensemble Summary
        print(f"\n{Colors.BOLD}{Colors.YELLOW}ENSEMBLE PREDICTION:{Colors.RESET}")
        print(f"  Multiplier: {Colors.get_multiplier_color(ensemble['predicted_multiplier'])}{ensemble['predicted_multiplier']:.2f}x{Colors.RESET}")
        print(f"  Confidence: {ensemble['confidence'] * 100:.0f}%")
        print(f"  Range: {ensemble['range'][0]:.2f}x - {ensemble['range'][1]:.2f}x")
        total_models = sum(len(v) for v in all_predictions.values())
        print(f"  Bet Consensus: {Colors.GREEN if ensemble['bet'] else Colors.RED}{ensemble['bet_votes']}/{total_models}{Colors.RESET} models recommend BET")

        # Hybrid Strategy
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}HYBRID BETTING STRATEGY:{Colors.RESET}")
        if hybrid['action'] == 'BET':
            print(f"  Position: {hybrid['position']}")
            print(f"  Action: {Colors.GREEN}{Colors.BOLD}BET{Colors.RESET}")
            print(f"  Target: {Colors.YELLOW}{hybrid['target_multiplier']:.1f}x{Colors.RESET}")
            print(f"  Confidence: {hybrid['confidence'] * 100:.0f}%")
            print(f"  Reason: {hybrid['reason']}")
        else:
            print(f"  Action: {Colors.GRAY}SKIP{Colors.RESET}")
            print(f"  Reason: {hybrid['reason']}")

        # Pattern Detection
        print(f"\n{Colors.BOLD}PATTERNS DETECTED:{Colors.RESET}")
        for pattern_name, pattern_data in patterns.items():
            if pattern_data.get('type'):
                conf = pattern_data.get('confidence', 0) * 100
                print(f"  {pattern_name.replace('_', ' ').title()}: {pattern_data['type']} ({conf:.0f}% confidence)")

        # Summary Statistics
        print(f"\n{Colors.BOLD}SUMMARY BY GROUP:{Colors.RESET}")
        # Legacy - DISABLED
        # if all_predictions.get('legacy'):
        #     legacy = all_predictions['legacy']
        #     legacy_avg = np.mean([m['predicted_multiplier'] for m in legacy])
        #     legacy_bets = sum(1 for m in legacy if m.get('bet', False))
        #     print(f"  Legacy ({len(legacy)} models):      Avg {legacy_avg:.2f}x,  Bets: {legacy_bets}/{len(legacy)}")

        if all_predictions.get('automl'):
            automl = all_predictions['automl']
            automl_avg = np.mean([m['predicted_multiplier'] for m in automl])
            automl_bets = sum(1 for m in automl if m.get('bet', False))
            print(f"  AutoML ({len(automl)} models):     Avg {automl_avg:.2f}x,  Bets: {automl_bets}/{len(automl)}")

        # Trained - DISABLED
        # if all_predictions.get('trained'):
        #     trained = all_predictions['trained']
        #     trained_avg = np.mean([m['predicted_multiplier'] for m in trained])
        #     trained_bets = sum(1 for m in trained if m.get('bet', False))
        #     print(f"  Trained ({len(trained)} models):      Avg {trained_avg:.2f}x,  Bets: {trained_bets}/{len(trained)}")

        print()
        print(f"{Colors.BOLD}FINAL RECOMMENDATION: {Colors.GREEN if hybrid['action'] == 'BET' else Colors.GRAY}{hybrid['action']}{Colors.RESET}")
        print("=" * 130)
        print()

    def update_step(self):
        """Single update step"""
        self.stats['total_updates'] += 1

        result = self.multiplier_reader.get_multiplier_with_status()

        if result['multiplier'] is None:
            self.stats['failed_reads'] += 1
            # Pass None to game_tracker to trigger crash detection
            events = self.game_tracker.update(None, 'UNKNOWN')

            # Log crash event if generated
            for event in events:
                self.log_event(event)

            # Check if round was just completed
            self.check_and_log_round_completion()
            return

        self.stats['successful_reads'] += 1
        multiplier = result['multiplier']
        status = result['status']

        # Update tracker and get events
        events = self.game_tracker.update(multiplier, status)

        # Log events
        for event in events:
            self.log_event(event)

        # Check if round was just completed (after crash event)
        self.check_and_log_round_completion()

        # Update stats
        if multiplier > self.stats['max_multiplier_ever']:
            self.stats['max_multiplier_ever'] = multiplier

        # Print current state
        round_summary = self.game_tracker.get_round_summary()
        self.print_status(multiplier, status, round_summary)

    def print_status(self, multiplier, status, round_summary):
        """Print status in a single dynamic line that updates in place"""
        if round_summary['status'] == 'RUNNING' and 'current_multiplier' in round_summary:
            duration = round_summary['duration']
            max_mult = round_summary['max_multiplier']
            current = round_summary['current_multiplier']
            round_num = self.game_tracker.round_number

            # Track multiplier history for sparkline
            self.multiplier_history.append(current)
            if len(self.multiplier_history) > self.max_history:
                self.multiplier_history.pop(0)

            # Generate sparkline
            sparkline = self.generate_sparkline(self.multiplier_history)

            # Get color based on multiplier
            color = Colors.get_multiplier_color(current)

            # Build status line - single line that updates dynamically
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_line = (
                f"\r{Colors.GRAY}[{timestamp}]{Colors.RESET} "
                f"{Colors.CYAN}R:{round_num+1}{Colors.RESET} | "
                f"{Colors.BOLD}CURR:{Colors.RESET} {color}{current:5.2f}x{Colors.RESET} | "
                f"{Colors.BOLD}MAX:{Colors.RESET} {Colors.MAGENTA}{max_mult:5.2f}x{Colors.RESET} | "
                f"{Colors.BOLD}DUR:{Colors.RESET} {duration:5.1f}s | "
                f"{Colors.BOLD}TREND:{Colors.RESET} {color}{sparkline}{Colors.RESET}"
            )

            # Print with carriage return to overwrite the same line
            # Use end='' to prevent newline, and flush to update immediately
            print(status_line, end='', flush=True)
            self.status_printed = True

    def print_stats(self):
        """Print statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        success_rate = (self.stats['successful_reads'] / self.stats['total_updates'] * 100) if self.stats['total_updates'] > 0 else 0

        print("\n")
        print("=" * 80)
        print("FINAL STATISTICS")
        print("=" * 80)
        print()

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Elapsed time: {elapsed:.1f}s")
        print(f"[{timestamp}] INFO: Total updates: {self.stats['total_updates']}")
        print(f"[{timestamp}] INFO: Successful reads: {self.stats['successful_reads']}")
        print(f"[{timestamp}] INFO: Failed reads: {self.stats['failed_reads']}")
        print(f"[{timestamp}] INFO: Success rate: {success_rate:.1f}%")
        print(f"[{timestamp}] INFO: Crashes detected: {self.stats['crashes_detected']}")
        print(f"[{timestamp}] INFO: Max multiplier ever: {self.stats['max_multiplier_ever']:.2f}x")

        # Show Supabase statistics
        if self.supabase.enabled:
            print(f"[{timestamp}] INFO: Supabase inserts: {self.stats['supabase_inserts']}")
            print(f"[{timestamp}] INFO: Supabase failures: {self.stats['supabase_failures']}")

        # Show ML prediction statistics
        if self.predictor and self.stats['predictions_made'] > 0:
            print()
            print(f"[{timestamp}] INFO: ML Predictions made: {self.stats['predictions_made']}")

            predictor_stats = self.predictor.get_statistics()
            if predictor_stats['predictions_made'] > 0:
                print(f"[{timestamp}] INFO: Average prediction error: {predictor_stats['avg_error']:.2f}x")
                print(f"[{timestamp}] INFO: Min prediction error: {predictor_stats['min_error']:.2f}x")
                print(f"[{timestamp}] INFO: Max prediction error: {predictor_stats['max_error']:.2f}x")

            if self.stats['prediction_errors']:
                avg_app_error = sum(self.stats['prediction_errors']) / len(self.stats['prediction_errors'])
                print(f"[{timestamp}] INFO: Session average error: {avg_app_error:.2f}x")

        print()

        # Print round history - DISABLED
        # if self.game_tracker.round_history:
        #     history_table = self.game_tracker.format_round_history_table(limit=None)
        #     print(history_table)
        # else:
        #     timestamp = datetime.now().strftime("%H:%M:%S")
        #     print(f"[{timestamp}] WARNING: No completed rounds yet.")

        print()

    def run(self):
        """Main run loop"""
        self.running = True
        print("=" * 80)
        print("MULTIPLIER READER")
        print("=" * 80)
        print()

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: Started")
        print(f"[{timestamp}] INFO: Region: ({self.region.x1}, {self.region.y1}) to ({self.region.x2}, {self.region.y2})")
        print(f"[{timestamp}] INFO: Update interval: {self.update_interval}s")
        print(f"[{timestamp}] INFO: Press Ctrl+C to stop")
        print()

        # Start auto-refresher
        self.auto_refresher.start()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: WAITING for first round...")

        try:
            while self.running:
                self.update_step()
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\n")
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Stopping multiplier reader...")

            # Stop auto-refresher
            self.auto_refresher.stop()

            self.print_stats()

if __name__ == "__main__":
    # Check for command line arguments
    interval = 0.5
    if len(sys.argv) > 1:
        try:
            interval = float(sys.argv[1])
        except ValueError:
            print("Usage: python main.py [update_interval_seconds]")
            sys.exit(1)

    app = MultiplierReaderApp(update_interval=interval)
    app.run()
