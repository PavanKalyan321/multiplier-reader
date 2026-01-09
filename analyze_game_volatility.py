#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aviator Game Volatility and Multiplier Analysis
Analyzes historical game data from Supabase to determine:
1. Game volatility (variance, unpredictability)
2. Frequency of max/very high multipliers
"""

import os
import sys
import io
from datetime import datetime
from typing import List, Dict, Tuple
import statistics
from supabase import create_client, Client

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Supabase credentials (from main.py)
SUPABASE_URL = 'https://zofojiubrykbtmstfhzx.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'


def connect_supabase() -> Client:
    """Connect to Supabase database"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Connected to Supabase successfully")
        return client
    except Exception as e:
        print(f"✗ Failed to connect to Supabase: {e}")
        sys.exit(1)


def fetch_all_rounds(client: Client) -> List[Dict]:
    """Fetch all historical rounds from betting_history table"""
    try:
        print("\nFetching betting history from Supabase...")

        # Try different table names that might exist
        table_names = ['betting_history', 'AviatorRound', 'rounds', 'game_rounds']

        for table_name in table_names:
            try:
                response = client.table(table_name).select('*').execute()
                if response.data:
                    print(f"✓ Found {len(response.data)} rounds in '{table_name}' table")
                    return response.data
            except:
                continue

        # If no table found, try with specific columns
        try:
            response = client.table('AviatorRound').select('roundId, multiplier, timestamp').execute()
            if response.data:
                print(f"✓ Found {len(response.data)} rounds in 'AviatorRound' table")
                return response.data
        except:
            pass

        print("✗ No betting history tables found in database")
        return []

    except Exception as e:
        print(f"✗ Failed to fetch rounds: {e}")
        return []


def calculate_statistics(multipliers: List[float]) -> Dict:
    """Calculate comprehensive statistics from multiplier data"""
    if not multipliers:
        return {}

    multipliers_sorted = sorted(multipliers)
    n = len(multipliers)

    # Basic stats
    min_mult = min(multipliers)
    max_mult = max(multipliers)
    mean_mult = statistics.mean(multipliers)
    median_mult = statistics.median(multipliers)

    # Variance and std dev
    variance = statistics.variance(multipliers) if n > 1 else 0
    std_dev = statistics.stdev(multipliers) if n > 1 else 0

    # Coefficient of variation (volatility measure)
    cv = (std_dev / mean_mult * 100) if mean_mult > 0 else 0

    # Quartiles
    q1 = multipliers_sorted[n // 4]
    q3 = multipliers_sorted[(3 * n) // 4]
    iqr = q3 - q1

    # High multiplier frequencies
    very_high_10x = sum(1 for m in multipliers if m >= 10.0)
    very_high_20x = sum(1 for m in multipliers if m >= 20.0)
    crash_rounds = sum(1 for m in multipliers if m < 1.2)

    # Distribution ranges
    range_1_1_5 = sum(1 for m in multipliers if 1.0 <= m < 1.5)
    range_1_5_2 = sum(1 for m in multipliers if 1.5 <= m < 2.0)
    range_2_3 = sum(1 for m in multipliers if 2.0 <= m < 3.0)
    range_3_5 = sum(1 for m in multipliers if 3.0 <= m < 5.0)
    range_5_10 = sum(1 for m in multipliers if 5.0 <= m < 10.0)
    range_10_plus = sum(1 for m in multipliers if m >= 10.0)

    return {
        'total_rounds': n,
        'min_multiplier': min_mult,
        'max_multiplier': max_mult,
        'range': max_mult - min_mult,
        'mean': mean_mult,
        'median': median_mult,
        'variance': variance,
        'std_dev': std_dev,
        'coefficient_variation': cv,
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'very_high_10x': very_high_10x,
        'very_high_20x': very_high_20x,
        'crash_rounds': crash_rounds,
        'pct_10x_plus': (very_high_10x / n * 100) if n > 0 else 0,
        'pct_20x_plus': (very_high_20x / n * 100) if n > 0 else 0,
        'pct_crash': (crash_rounds / n * 100) if n > 0 else 0,
        'distribution': {
            '1.0-1.5x': {'count': range_1_1_5, 'pct': (range_1_1_5 / n * 100) if n > 0 else 0},
            '1.5-2.0x': {'count': range_1_5_2, 'pct': (range_1_5_2 / n * 100) if n > 0 else 0},
            '2.0-3.0x': {'count': range_2_3, 'pct': (range_2_3 / n * 100) if n > 0 else 0},
            '3.0-5.0x': {'count': range_3_5, 'pct': (range_3_5 / n * 100) if n > 0 else 0},
            '5.0-10x': {'count': range_5_10, 'pct': (range_5_10 / n * 100) if n > 0 else 0},
            '10.0x+': {'count': range_10_plus, 'pct': (range_10_plus / n * 100) if n > 0 else 0},
        }
    }


def get_volatility_assessment(cv: float) -> str:
    """Determine volatility level from coefficient of variation"""
    if cv < 30:
        return "LOW - Very stable, predictable game"
    elif cv < 50:
        return "MODERATE - Some variance but manageable"
    elif cv < 80:
        return "HIGH - Volatile, unpredictable"
    else:
        return "VERY HIGH - Extremely volatile, very unpredictable"


def print_analysis_report(stats: Dict):
    """Print formatted analysis report"""

    print("\n" + "=" * 80)
    print("AVIATOR GAME VOLATILITY & MULTIPLIER ANALYSIS".center(80))
    print("=" * 80)

    if not stats:
        print("No data available for analysis")
        return

    print(f"\n📊 DATASET OVERVIEW")
    print("-" * 80)
    print(f"  Total Rounds Analyzed:       {stats['total_rounds']:,} rounds")
    print(f"  Multiplier Range:            {stats['min_multiplier']:.2f}x - {stats['max_multiplier']:.2f}x")
    print(f"  Range Span:                  {stats['range']:.2f}x")

    print(f"\n📈 CENTRAL TENDENCY & DISTRIBUTION")
    print("-" * 80)
    print(f"  Mean Multiplier:             {stats['mean']:.2f}x")
    print(f"  Median Multiplier:           {stats['median']:.2f}x")
    print(f"  Q1 (25th percentile):        {stats['q1']:.2f}x")
    print(f"  Q3 (75th percentile):        {stats['q3']:.2f}x")
    print(f"  Interquartile Range (IQR):   {stats['iqr']:.2f}x")

    print(f"\n⚡ VOLATILITY MEASURES")
    print("-" * 80)
    print(f"  Variance:                    {stats['variance']:.2f}")
    print(f"  Standard Deviation:          {stats['std_dev']:.2f}x")
    print(f"  Coefficient of Variation:    {stats['coefficient_variation']:.1f}%")
    print(f"  Volatility Assessment:       {get_volatility_assessment(stats['coefficient_variation'])}")

    print(f"\n🎯 MAX/VERY HIGH MULTIPLIER FREQUENCY")
    print("-" * 80)
    print(f"  Rounds with 10x+ multipliers:")
    print(f"    Count: {stats['very_high_10x']:,} rounds")
    print(f"    Frequency: {stats['pct_10x_plus']:.2f}% of all rounds")
    print(f"    Roughly 1 in every {int(100/stats['pct_10x_plus']) if stats['pct_10x_plus'] > 0 else 'N/A'} rounds")

    print(f"\n  Rounds with 20x+ multipliers:")
    print(f"    Count: {stats['very_high_20x']:,} rounds")
    print(f"    Frequency: {stats['pct_20x_plus']:.2f}% of all rounds")
    print(f"    Roughly 1 in every {int(100/stats['pct_20x_plus']) if stats['pct_20x_plus'] > 0 else 'N/A'} rounds")

    print(f"\n💥 CRASH ROUNDS (< 1.2x)")
    print("-" * 80)
    print(f"  Count: {stats['crash_rounds']:,} rounds")
    print(f"  Frequency: {stats['pct_crash']:.2f}% of all rounds")

    print(f"\n📊 MULTIPLIER DISTRIBUTION")
    print("-" * 80)
    for range_label, data in stats['distribution'].items():
        bar_length = int(data['pct'] / 5)  # Scale to 20 chars max
        bar = "█" * bar_length
        print(f"  {range_label:12} | {bar:<20} | {data['count']:6,} rounds ({data['pct']:5.1f}%)")

    print("\n" + "=" * 80)
    print("VOLATILITY CONCLUSION".center(80))
    print("=" * 80)

    cv = stats['coefficient_variation']
    pct_10x = stats['pct_10x_plus']
    pct_20x = stats['pct_20x_plus']

    print(f"\n1️⃣  GAME VOLATILITY ANSWER:")
    print(f"    {get_volatility_assessment(cv)}")
    print(f"    (CV = {cv:.1f}% indicates {('very ' if cv > 80 else '')}")
    print(f"    {'HIGH' if cv > 80 else 'MODERATE' if cv > 50 else 'LOW'} variance and unpredictability)")

    print(f"\n2️⃣  MAX/VERY HIGH MULTIPLIER FREQUENCY:")
    print(f"    10x+ multipliers appear in {pct_10x:.2f}% of rounds")
    print(f"    ({pct_10x / 5:.1f}% are in the ultra-high 10x+ range)")
    print(f"    ")
    print(f"    20x+ multipliers appear in {pct_20x:.2f}% of rounds")
    print(f"    (Extremely rare {pct_20x / 5:.1f}% occurrence rate)")

    if pct_10x > 10:
        print(f"\n    ✓ Game gives high multipliers FREQUENTLY (> 10% occurrence)")
    elif pct_10x > 5:
        print(f"\n    ⚠ Game gives high multipliers MODERATELY (5-10% occurrence)")
    else:
        print(f"\n    ✗ Game gives high multipliers RARELY (< 5% occurrence)")

    print("\n" + "=" * 80)


def main():
    """Main analysis function"""
    print("Aviator Game Volatility Analyzer")
    print("=" * 80)

    # Connect to Supabase
    client = connect_supabase()

    # Fetch all rounds
    rounds = fetch_all_rounds(client)

    if not rounds:
        print("\n✗ No game data found in database. Please ensure betting_history has been recorded.")
        sys.exit(1)

    # Extract multipliers
    multipliers = []
    for round_data in rounds:
        # Handle different possible column names
        mult = round_data.get('multiplier') or round_data.get('crash_multiplier') or round_data.get('payout')
        if mult is not None:
            try:
                multipliers.append(float(mult))
            except (ValueError, TypeError):
                continue

    if not multipliers:
        print("\n✗ No multiplier data found in records")
        sys.exit(1)

    print(f"✓ Extracted {len(multipliers)} multiplier values")

    # Calculate statistics
    stats = calculate_statistics(multipliers)

    # Print report
    print_analysis_report(stats)


if __name__ == '__main__':
    main()
