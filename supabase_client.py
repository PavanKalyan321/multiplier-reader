# Supabase client for storing round data
from supabase import create_client, Client
from datetime import datetime
import os


class SupabaseLogger:
    """Handle Supabase database operations for round data"""

    def __init__(self, url=None, key=None):
        """Initialize Supabase client with credentials"""
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        self.client: Client = None
        self.enabled = False

        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                self.enabled = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Supabase connected successfully")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Supabase connection failed: {e}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Continuing with local logging only")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Supabase credentials not provided, using local logging only")

    def insert_round(self, round_number, multiplier, timestamp=None):
        """
        Insert round data into AviatorRound table

        Args:
            round_number (int): Round identifier
            multiplier (float): Final/crash multiplier value
            timestamp (datetime): Round end timestamp (defaults to now)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Prepare data matching AviatorRound schema
            data = {
                'roundid': round_number,
                'multiplier': multiplier,
                'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat()
            }

            # Insert into AviatorRound table
            response = self.client.table('AviatorRound').insert(data).execute()

            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Round {round_number} saved to Supabase (multiplier: {multiplier:.2f}x)")
            return True

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to save round to Supabase: {e}")
            return False
