# Simple test to insert one entry into AviatorRound table
from supabase_client import SupabaseLogger
from datetime import datetime

print("=" * 80)
print("TEST: Insert Single Entry into AviatorRound Table")
print("=" * 80)
print()

# Initialize Supabase
supabase = SupabaseLogger(
    url='https://zofojiubrykbtmstfhzx.supabase.co',
    key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s'
)

print()
print("Preparing test data...")
test_multiplier = 2.45
test_timestamp = datetime.now()

print(f"  Multiplier: {test_multiplier}x")
print(f"  Timestamp: {test_timestamp}")
print()

print("-" * 80)
print("Attempting to insert into AviatorRound table...")
print("-" * 80)
print()

# Try to insert
round_id = supabase.insert_round(
    round_number=1,  # Just for logging purposes
    multiplier=test_multiplier,
    timestamp=test_timestamp
)

print()
print("=" * 80)

if round_id:
    print("SUCCESS!")
    print("=" * 80)
    print()
    print(f"Round inserted successfully!")
    print(f"Auto-generated roundId: {round_id}")
    print()
    print("Verify in Supabase SQL Editor:")
    print()
    print(f"SELECT * FROM \"AviatorRound\" WHERE \"roundId\" = {round_id};")
    print()
    print("Expected result:")
    print(f"  roundId: {round_id}")
    print(f"  multiplier: {test_multiplier}")
    print(f"  timestamp: {test_timestamp.isoformat()}")
    print()
else:
    print("FAILED!")
    print("=" * 80)
    print()
    print("The insert did not succeed. Check the error message above.")
    print()
    print("Most likely cause:")
    print("  The trigger 'after_insert_analytics_generate' is causing an error")
    print()
    print("Quick fix:")
    print("  1. Open Supabase SQL Editor")
    print("  2. Run this SQL:")
    print()
    print("     ALTER TABLE \"AviatorRound\" DISABLE TRIGGER after_insert_analytics_generate;")
    print()
    print("  3. Run this test script again")
    print()

print("=" * 80)
