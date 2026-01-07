#!/usr/bin/env python
"""Test Azure Foundry integration and verify database insertion"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def test_health():
    """Test Azure service health"""
    endpoint = os.getenv('AZURE_FOUNDRY_ENDPOINT')

    print("=" * 60)
    print("TESTING AZURE AI FOUNDRY SERVICE")
    print("=" * 60)
    print(f"\nEndpoint: {endpoint}")

    try:
        response = requests.get(f"{endpoint}/health", timeout=5)

        if response.status_code == 200:
            health = response.json()
            print(f"\n[OK] Service Status: {health.get('status')}")
            print(f"[OK] Models Loaded: {health.get('models_loaded', 0)}")
            print(f"[OK] Supabase Connected: {health.get('supabase_connected', False)}")

            if health.get('supabase_connected'):
                print("\n*** SUPABASE IS CONNECTED! ***")
            else:
                print("\n[X] SUPABASE NOT CONNECTED")
                print("Check Azure environment variables!")

            return health.get('supabase_connected', False)
        else:
            print(f"\n[X] Service returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"\n[X] Error connecting to service: {e}")
        return False

def test_prediction():
    """Test prediction endpoint"""
    endpoint = os.getenv('AZURE_FOUNDRY_ENDPOINT')

    print("\n" + "=" * 60)
    print("TESTING PREDICTION ENDPOINT")
    print("=" * 60)

    try:
        payload = {
            "round_id": 99999,  # Test round ID
            "round_number": 1
        }

        print(f"\nSending test prediction request...")
        response = requests.post(
            f"{endpoint}/predict",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n[OK] Prediction Status: {result.get('status')}")
            print(f"[OK] Signal ID: {result.get('signal_id')}")
            print(f"[OK] Models Executed: {result.get('models_executed', 0)}/15")
            print(f"[OK] Confidence: {result.get('ensemble_confidence', 0):.1%}")

            if result.get('signal_id') is not None:
                print(f"\n*** ANALYTICS SIGNAL SAVED! (ID: {result.get('signal_id')}) ***")
                print("\nYou should now see this entry in analytics_round_signals table!")
                return True
            else:
                print("\n[X] Signal ID is None - not saving to database")
                return False
        else:
            print(f"\n[X] Request failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"\n[X] Error testing prediction: {e}")
        return False

if __name__ == "__main__":
    print(f"\nTest started at: {datetime.now().strftime('%H:%M:%S')}\n")

    # Test 1: Health check
    supabase_connected = test_health()

    # Test 2: Prediction (only if Supabase is connected)
    if supabase_connected:
        test_prediction()
    else:
        print("\n⚠ Skipping prediction test - Supabase not connected")
        print("\nTO FIX:")
        print("1. Go to Azure Portal")
        print("2. Container Apps → Your App → Settings → Environment Variables")
        print("3. Add SUPABASE_URL and SUPABASE_KEY")
        print("4. Restart the container")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
