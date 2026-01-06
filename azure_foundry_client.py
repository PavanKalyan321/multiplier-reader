"""
Azure AI Foundry Client
Communicates with Azure AI Foundry service for predictions
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, Optional


class AzureFoundryClient:
    """HTTP client for Azure AI Foundry prediction service"""

    def __init__(self, endpoint_url: str = None, api_key: str = None, timeout: int = 15):
        """
        Initialize Azure AI Foundry client

        Args:
            endpoint_url: Azure Container App endpoint URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.endpoint_url = endpoint_url or os.getenv('AZURE_FOUNDRY_ENDPOINT', '')
        self.api_key = api_key or os.getenv('AZURE_FOUNDRY_API_KEY', '')
        self.timeout = timeout
        self.enabled = bool(self.endpoint_url and self.api_key)

        if self.enabled:
            # Clean up endpoint URL
            self.endpoint_url = self.endpoint_url.rstrip('/')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Azure AI Foundry client initialized")
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Endpoint: {self.endpoint_url}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Azure AI Foundry disabled - credentials not provided")

    def request_prediction(self, round_id: int, round_number: int) -> Dict:
        """
        Request prediction from Azure AI Foundry service

        Args:
            round_id: Unique round identifier
            round_number: Sequential round number

        Returns:
            Dict with status, signal_id, models_executed, ensemble_confidence
        """
        if not self.enabled:
            return {
                'status': 'error',
                'error': 'Azure AI Foundry not enabled'
            }

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] INFO: Requesting prediction from Azure AI Foundry...")

            # Prepare request
            url = f"{self.endpoint_url}/predict"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            payload = {
                'round_id': round_id,
                'round_number': round_number
            }

            # Send request
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            # Check response status
            if response.status_code == 200:
                result = response.json()
                print(f"[{timestamp}] ✓ Azure prediction received")
                print(f"[{timestamp}]   - Models: {result.get('models_executed', 0)}/15")
                print(f"[{timestamp}]   - Confidence: {result.get('ensemble_confidence', 0):.0%}")
                return result
            else:
                error_msg = f"Azure returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass

                print(f"[{timestamp}] WARNING: {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg
                }

        except requests.Timeout:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Azure request timeout ({self.timeout}s)")
            return {
                'status': 'error',
                'error': f'Request timeout after {self.timeout}s'
            }

        except requests.ConnectionError as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Azure connection error: {e}")
            return {
                'status': 'error',
                'error': f'Connection error: {str(e)}'
            }

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] WARNING: Azure request failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def check_health(self) -> bool:
        """
        Check if Azure service is healthy

        Returns:
            True if service is available and healthy
        """
        if not self.enabled:
            return False

        try:
            url = f"{self.endpoint_url}/health"
            response = requests.get(
                url,
                timeout=5
            )

            if response.status_code == 200:
                health_data = response.json()
                return health_data.get('status') == 'healthy'

            return False

        except Exception:
            return False

    def get_model_status(self) -> Dict:
        """
        Get status of all models in Azure service

        Returns:
            Dict with model statuses
        """
        if not self.enabled:
            return {'status': 'disabled'}

        try:
            url = f"{self.endpoint_url}/health"
            response = requests.get(
                url,
                timeout=5
            )

            if response.status_code == 200:
                return response.json()

            return {'status': 'unavailable'}

        except Exception as e:
            return {'status': 'error', 'error': str(e)}
