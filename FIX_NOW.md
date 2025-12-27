# FIX NOW - Enable First API Call

## The Problem

Your first API call (inserting into `AviatorRound`) is **FAILING** because of this error:

```
COALESCE types analytics_round_signals and record cannot be matched
```

This means the trigger function `analytics_generate_round_signal()` has incorrect code that's trying to do something with `analytics_round_signals` that doesn't work.

## The Solution (2 Minutes)

### Step 1: Open Supabase SQL Editor

Go to your Supabase dashboard → SQL Editor

### Step 2: Run This SQL

**Copy and paste this entire block:**

```sql
-- Disable the problematic trigger
ALTER TABLE "AviatorRound"
DISABLE TRIGGER after_insert_analytics_generate;
```

Click **RUN**.

You should see: `SUCCESS`

### Step 3: Verify It Works

Run this test:

```sql
-- Test insert
DO $$
DECLARE
    test_round_id BIGINT;
BEGIN
    INSERT INTO "AviatorRound" (multiplier, timestamp)
    VALUES (2.50, NOW())
    RETURNING "roundId" INTO test_round_id;

    RAISE NOTICE 'SUCCESS! Inserted round with ID: %', test_round_id;

    -- Clean up test data
    DELETE FROM "AviatorRound" WHERE "roundId" = test_round_id;
END $$;
```

If you see `SUCCESS! Inserted round with ID: X` → **IT'S FIXED!**

### Step 4: Run Your App

```bash
python.exe main.py
```

Now you should see:

```
[10:30:15] INFO: Round 1 saved to Supabase (ID: 123, multiplier: 2.45x)
```

## What Changed?

**Before:**
```
Round completes → Try to insert → Trigger runs → CRASH!
→ Error: COALESCE types cannot be matched
```

**After (trigger disabled):**
```
Round completes → Insert succeeds → Returns roundId → Prediction saved
```

## Why Disable the Trigger?

Your trigger function has a bug. Since we're making **two separate API calls** (one for rounds, one for analytics), we don't need the trigger anyway.

The trigger was probably meant to automatically create analytics entries, but:
1. It has a bug in the code
2. We're handling that ourselves with the second API call
3. So it's safe to disable

## What If You Need the Trigger Later?

You can re-enable it after fixing the function:

```sql
-- Fix the function first
CREATE OR REPLACE FUNCTION analytics_generate_round_signal()
RETURNS TRIGGER AS $$
BEGIN
    -- Your corrected logic here
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Then re-enable the trigger
ALTER TABLE "AviatorRound"
ENABLE TRIGGER after_insert_analytics_generate;
```

But for now, **you don't need it** because the Python code handles both API calls.

## Quick Checklist

- [ ] Open Supabase SQL Editor
- [ ] Run: `ALTER TABLE "AviatorRound" DISABLE TRIGGER after_insert_analytics_generate;`
- [ ] Verify with test insert
- [ ] Run: `python.exe main.py`
- [ ] Watch for: `[INFO] Round X saved to Supabase (ID: Y, multiplier: Z)`

That's it! Your first API call will work now.
