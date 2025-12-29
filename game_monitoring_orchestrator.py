"""
Game Monitoring Orchestrator - Game Monitoring & Crash Detection

Handles:
1. Waiting for game start (multiplier > 1.05x)
2. Monitoring multiplier to target
3. Crash detection
4. Progress display
5. Data collection
"""

import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class GameMonitor:
    """Monitors game multiplier with crash detection"""

    def __init__(self, multiplier_reader: Any, game_tracker: Optional[Any] = None,
                 sampling_interval: float = 0.03):
        """
        Initialize game monitor

        Args:
            multiplier_reader: MultiplierReader instance
            game_tracker: GameTracker instance (optional)
            sampling_interval: Sampling interval in seconds (default 30ms)
        """
        self.multiplier_reader = multiplier_reader
        self.game_tracker = game_tracker
        self.sampling_interval = sampling_interval  # 0.03 = 30ms

    def wait_for_game_start(self, timeout: float = 15.0,
                           start_threshold: float = 1.05) -> Tuple[bool, Optional[float], float]:
        """
        Wait for game to start (multiplier > threshold)

        Args:
            timeout: Maximum wait time in seconds
            start_threshold: Multiplier threshold for game start (default 1.05x)

        Returns:
            Tuple of (started: bool, start_multiplier: float, elapsed_time: float)
        """
        start_time = time.time()
        last_display = 0

        while True:
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > timeout:
                return False, None, elapsed

            # Read current multiplier
            current_mult = self.multiplier_reader.read_multiplier()

            # Game started when multiplier exceeds threshold
            if current_mult and current_mult > start_threshold:
                return True, current_mult, elapsed

            # Display progress every 0.5 seconds
            if elapsed - last_display >= 0.5:
                print(f"  Waiting for game start... ({elapsed:.1f}s)")
                last_display = elapsed

            time.sleep(self.sampling_interval)

    def monitor_to_target(self, target_multiplier: float,
                         timeout: float = 60.0,
                         display_interval: float = 0.5) -> Dict:
        """
        Monitor multiplier until target reached or game crashes

        Args:
            target_multiplier: Target multiplier value
            timeout: Maximum monitoring duration
            display_interval: Display update interval

        Returns:
            Dict with monitoring results
        """
        start_time = time.time()
        last_display = 0
        max_multiplier = 0
        samples_collected = []
        crash_detected = False
        crash_point = None
        target_reached = False

        print(f"  Monitoring to {target_multiplier:.2f}x (timeout: {timeout}s)")

        while True:
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > timeout:
                break

            # Read current multiplier
            current_mult = self.multiplier_reader.read_multiplier()

            # Sample collection
            if current_mult is not None:
                samples_collected.append({
                    'timestamp': elapsed,
                    'multiplier': current_mult
                })
                max_multiplier = max(max_multiplier, current_mult)

                # Crash detection: multiplier drops to 0 or becomes None
                if current_mult == 0 or current_mult < 0.99:
                    if not crash_detected:
                        crash_detected = True
                        crash_point = current_mult if current_mult else max_multiplier
                        break

                # Target detection
                if current_mult >= target_multiplier and not target_reached:
                    target_reached = True
                    print(f"  Target reached: {current_mult:.2f}x >= {target_multiplier:.2f}x")
                    break

            # Display progress
            if elapsed - last_display >= display_interval:
                if current_mult:
                    progress_pct = (current_mult / target_multiplier) * 100
                    print(f"    {elapsed:.1f}s | Multiplier: {current_mult:.2f}x ({progress_pct:.1f}%)")
                last_display = elapsed

            time.sleep(self.sampling_interval)

        # Final multiplier value
        final_multiplier = samples_collected[-1]['multiplier'] if samples_collected else 0

        monitoring_result = {
            'game_started': True,
            'target_reached': target_reached,
            'max_multiplier_observed': max_multiplier,
            'final_multiplier': final_multiplier,
            'samples_collected': len(samples_collected),
            'crash_detected': crash_detected,
            'crash_point': crash_point,
            'monitoring_duration': elapsed,
            'timeout': timeout,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return monitoring_result

    def detect_crash(self, current_mult: Optional[float],
                    prev_mult: Optional[float]) -> bool:
        """
        Detect game crash (multiplier drops significantly or becomes 0)

        Args:
            current_mult: Current multiplier reading
            prev_mult: Previous multiplier reading

        Returns:
            bool indicating crash detected
        """
        if current_mult is None:
            return True

        if current_mult == 0:
            return True

        if prev_mult is not None and current_mult < 0.99 * prev_mult:
            return True

        return False


class GameMonitoringOrchestrator:
    """Orchestrates game monitoring phase"""

    def __init__(self, monitor: GameMonitor):
        """Initialize orchestrator"""
        self.monitor = monitor

    def execute_monitoring_phase(self, target_multiplier: float) -> Dict:
        """
        Execute full game monitoring workflow

        Includes:
        1. Wait for game start
        2. Monitor to target multiplier
        3. Collect data
        4. Detect crashes

        Args:
            target_multiplier: Target multiplier to reach

        Returns:
            Dict with complete monitoring results
        """
        # Phase 1: Wait for game start
        print("Waiting for game to start...")
        game_started, start_mult, start_time = self.monitor.wait_for_game_start(
            timeout=15.0,
            start_threshold=1.05
        )

        if not game_started:
            return {
                'success': False,
                'error': 'game_start_timeout',
                'elapsed': start_time,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        print(f"Game started at {start_mult:.2f}x after {start_time:.2f}s")

        # Phase 2: Monitor to target
        monitoring_result = self.monitor.monitor_to_target(
            target_multiplier=target_multiplier,
            timeout=60.0,
            display_interval=0.5
        )

        # Phase 3: Determine outcome
        if monitoring_result['crash_detected']:
            outcome = 'CRASH'
        elif monitoring_result['target_reached']:
            outcome = 'TARGET_REACHED'
        else:
            outcome = 'TIMEOUT'

        complete_result = {
            'success': True,
            'outcome': outcome,
            'game_started': game_started,
            'start_multiplier': start_mult,
            'start_time': start_time,
            'target_multiplier': target_multiplier,
            'final_multiplier': monitoring_result['final_multiplier'],
            'max_multiplier': monitoring_result['max_multiplier_observed'],
            'crash_detected': monitoring_result['crash_detected'],
            'crash_point': monitoring_result['crash_point'],
            'target_reached': monitoring_result['target_reached'],
            'duration': monitoring_result['monitoring_duration'],
            'samples_collected': monitoring_result['samples_collected'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return complete_result
