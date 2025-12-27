# Fix AviatorRound Table - Step by Step Guide

## The Problem

You're getting this error:
```
[WARNING] Failed to save round to Supabase: {'message': 'column "m_std" does not exist', 'code': '42703'}
```

This means your Supabase `AviatorRound` table has a **database trigger or function** that's trying to use a column called `m_std` (probably for "multiplier standard deviation") that doesn't exist.

## Solution Options

### Option 1: Quick Fix - Drop and Recreate Table (LOSES DATA)

**Use this if you don't care about existing data**

1. Open Supabase SQL Editor
2. Run [FIX_AVIATOR_ROUND_TABLE.sql](FIX_AVIATOR_ROUND_TABLE.sql)
3. This will create a clean table with only the columns we need

### Option 2: Keep Your Data - Remove Triggers

**Use this if you want to keep existing rounds**

1. Open Supabase SQL Editor
2. Run [FIX_AVIATOR_ROUND_KEEP_DATA.sql](FIX_AVIATOR_ROUND_KEEP_DATA.sql) step by step
3. Follow the comments in the SQL to:
   - Find problematic triggers
   - Drop them
   - Test insert

## Testing the Fix

### Step 1: Run Test Version Without ML

```bash
python.exe main_no_ml.py
```

This version:
- ✅ Reads multipliers
- ✅ Tracks rounds
- ✅ Saves to Supabase
- ❌ NO ML predictions (to isolate the issue)

### Step 2: Watch for Success Message

When a round completes, you should see:

```
[10:15:30] INFO: Attempting to save round to Supabase...
[10:15:30] DEBUG: Round #1
[10:15:30] DEBUG: Multiplier: 2.45x
[10:15:30] DEBUG: Timestamp: 2024-12-24T10:15:30
[10:15:30] INFO: Round 1 saved to Supabase (multiplier: 2.45x)
[10:15:30] ✅ SUCCESS: Round saved to Supabase
```

### Step 3: Verify in Supabase

Run this query in Supabase SQL Editor:

```sql
SELECT * FROM "AviatorRound" ORDER BY "timestamp" DESC LIMIT 10;
```

You should see your rounds!

## Common Issues and Solutions

### Issue 1: "column m_std does not exist"

**Cause:** Database trigger trying to calculate standard deviation

**Solution:**
```sql
-- Find triggers
SELECT tgname FROM pg_trigger WHERE tgrelid = '"AviatorRound"'::regclass;

-- Drop the trigger (replace 'trigger_name' with actual name)
DROP TRIGGER IF EXISTS trigger_name ON "AviatorRound";
```

### Issue 2: "permission denied"

**Cause:** RLS (Row Level Security) policies

**Solution:**
```sql
-- Disable RLS temporarily for testing
ALTER TABLE "AviatorRound" DISABLE ROW LEVEL SECURITY;
```

### Issue 3: Still getting errors

**Solution:** Use the nuclear option - drop and recreate:

```sql
DROP TABLE IF EXISTS "AviatorRound" CASCADE;

CREATE TABLE "AviatorRound" (
    "roundId" BIGINT PRIMARY KEY,
    "multiplier" REAL NOT NULL,
    "timestamp" TIMESTAMP DEFAULT NOW()
);
```

## What We're Trying to Insert

The code only inserts these 3 fields:

```python
data = {
    'roundId': 20241224101530123,      # Timestamp-based unique ID
    'multiplier': 2.45,                 # Crash multiplier
    'timestamp': '2024-12-24T10:15:30'  # ISO timestamp
}
```

**Nothing else!** No `m_std`, no calculated columns, nothing.

## Table Should Look Like This

```
┌────────────────────┬─────────────┬─────────────────────┐
│ roundId            │ multiplier  │ timestamp           │
├────────────────────┼─────────────┼─────────────────────┤
│ 20241224101530123  │ 2.45        │ 2024-12-24 10:15:30 │
│ 20241224101545789  │ 3.21        │ 2024-12-24 10:15:45 │
│ 20241224101602456  │ 1.89        │ 2024-12-24 10:16:02 │
└────────────────────┴─────────────┴─────────────────────┘
```

## Once Rounds Table Works

After you confirm rounds are saving successfully:

1. Stop the test version: `Ctrl+C`
2. Create the ML predictions table (run [SUPABASE_PREDICTIONS_TABLE.sql](SUPABASE_PREDICTIONS_TABLE.sql))
3. Run the full version: `python.exe main.py`

## Files Created for You

1. **[FIX_AVIATOR_ROUND_TABLE.sql](FIX_AVIATOR_ROUND_TABLE.sql)** - Drop and recreate (loses data)
2. **[FIX_AVIATOR_ROUND_KEEP_DATA.sql](FIX_AVIATOR_ROUND_KEEP_DATA.sql)** - Fix while keeping data
3. **[main_no_ml.py](main_no_ml.py)** - Test version without ML predictions

## Quick Checklist

- [ ] Open Supabase SQL Editor
- [ ] Run one of the fix SQL scripts
- [ ] Verify table structure with `SELECT * FROM "AviatorRound" LIMIT 1;`
- [ ] Run test version: `python.exe main_no_ml.py`
- [ ] Wait for one round to complete
- [ ] Check for ✅ SUCCESS message
- [ ] Verify in Supabase that round was saved
- [ ] Once working, create predictions table
- [ ] Run full version: `python.exe main.py`

---

**Need Help?**

The error message tells you exactly what's wrong. Look for keywords:
- `"m_std" does not exist` → Trigger/function issue
- `permission denied` → RLS policy issue
- `duplicate key` → roundId collision (rare)
