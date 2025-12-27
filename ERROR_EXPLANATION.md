# Why You Can't See the First API Call

## The Error

```
COALESCE types analytics_round_signals and record cannot be matched
```

## What's Happening

```
┌─────────────────────────────────────────────────────────────┐
│  Your Python Code Tries to Insert Round                    │
│                                                             │
│  supabase.insert_round(multiplier=2.45, timestamp=now)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Supabase Receives Request                                  │
│  INSERT INTO "AviatorRound" (multiplier, timestamp)         │
│  VALUES (2.45, '2024-12-24 10:15:30')                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  BEFORE Insert Happens...                                   │
│  Trigger Fires: after_insert_analytics_generate             │
│  Calls Function: analytics_generate_round_signal()          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ❌ FUNCTION HAS A BUG!                                      │
│  Code tries to:                                             │
│  COALESCE(something, analytics_round_signals)               │
│                                                             │
│  Error: Can't COALESCE a record type with a table name!    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Insert FAILS - Transaction Rolls Back                      │
│  No data is inserted                                        │
│  Python code receives error                                 │
│  You never see: "Round saved to Supabase"                   │
└─────────────────────────────────────────────────────────────┘
```

## The Trigger Function Bug

Your trigger function `analytics_generate_round_signal()` probably has code like this:

```sql
CREATE OR REPLACE FUNCTION analytics_generate_round_signal()
RETURNS TRIGGER AS $$
BEGIN
    -- WRONG CODE - This causes the error:
    INSERT INTO analytics_round_signals (...)
    VALUES (
        ...,
        COALESCE(NEW, analytics_round_signals),  -- ❌ BUG HERE
        ...
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

The problem: `COALESCE(NEW, analytics_round_signals)` doesn't make sense because:
- `NEW` is a record (the row being inserted)
- `analytics_round_signals` is a **table name**, not a value

PostgreSQL says: "I can't match these types!"

## How to See the Actual Function

Run this in Supabase to see what the function actually does:

```sql
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'analytics_generate_round_signal';
```

## The Fix

Since we're making **two separate API calls** in Python, we don't need this trigger at all.

**Disable it:**

```sql
ALTER TABLE "AviatorRound"
DISABLE TRIGGER after_insert_analytics_generate;
```

**Result:**

```
┌─────────────────────────────────────────────────────────────┐
│  Your Python Code Tries to Insert Round                    │
│  supabase.insert_round(multiplier=2.45, timestamp=now)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Supabase Receives Request                                  │
│  INSERT INTO "AviatorRound" (multiplier, timestamp)         │
│  VALUES (2.45, '2024-12-24 10:15:30')                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Trigger is DISABLED - Skipped!                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ✅ INSERT SUCCEEDS!                                         │
│  Row inserted with auto-generated roundId = 123             │
│  Returns: {"roundId": 123, "multiplier": 2.45, ...}         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Python receives roundId = 123                              │
│  Prints: "Round 1 saved to Supabase (ID: 123, ...)"         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Second API Call - Insert Analytics Signal                  │
│  Uses roundId = 123 to link prediction to round             │
│  SUCCESS!                                                   │
└─────────────────────────────────────────────────────────────┘
```

## Summary

**Why you can't see the first API call:**
- Trigger has a bug → Insert fails → Nothing is saved → No output

**Fix:**
- Disable the trigger → Insert succeeds → You see the output

**File to use:**
- [DISABLE_TRIGGER_NOW.sql](DISABLE_TRIGGER_NOW.sql) - Copy and paste into Supabase SQL Editor

**Then:**
- Run `python.exe main.py`
- You'll now see: `[INFO] Round X saved to Supabase (ID: Y, multiplier: Z)`
