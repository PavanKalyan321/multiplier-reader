-- SQL Script to Fix AviatorRound Table (KEEP EXISTING DATA)
-- Run this in your Supabase SQL Editor

-- Step 1: Find and list all triggers on AviatorRound table
SELECT
    tgname AS trigger_name,
    pg_get_triggerdef(oid) AS trigger_definition
FROM pg_trigger
WHERE tgrelid = '"AviatorRound"'::regclass;

-- Step 2: Drop problematic triggers
-- Look for triggers that reference 'm_std' or other missing columns
-- Uncomment and modify these lines based on what you find in Step 1:

-- DROP TRIGGER IF EXISTS calculate_stats ON "AviatorRound";
-- DROP TRIGGER IF EXISTS update_aggregates ON "AviatorRound";
-- DROP TRIGGER IF EXISTS compute_statistics ON "AviatorRound";

-- Step 3: Check if m_std column exists
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'AviatorRound'
ORDER BY ordinal_position;

-- Step 4: If m_std column is needed by something, either:
-- Option A: Add the column
-- ALTER TABLE "AviatorRound" ADD COLUMN IF NOT EXISTS "m_std" REAL DEFAULT NULL;

-- Option B: Drop the column if it exists but shouldn't
-- ALTER TABLE "AviatorRound" DROP COLUMN IF EXISTS "m_std";

-- Step 5: Verify the table only has the columns we need
-- Should only see: roundId, multiplier, timestamp, (and maybe created_at)

-- Step 6: Test insert
DO $$
DECLARE
    test_id BIGINT := 99999999999999;
BEGIN
    -- Try to insert
    INSERT INTO "AviatorRound" ("roundId", "multiplier", "timestamp")
    VALUES (test_id, 2.50, NOW());

    -- If successful, clean up
    DELETE FROM "AviatorRound" WHERE "roundId" = test_id;

    RAISE NOTICE 'Test insert successful! Table is fixed.';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Test insert failed: %', SQLERRM;
        -- Try to clean up anyway
        DELETE FROM "AviatorRound" WHERE "roundId" = test_id;
END $$;

-- Step 7: Check current data count
SELECT
    COUNT(*) as total_rounds,
    MIN("multiplier") as min_multiplier,
    MAX("multiplier") as max_multiplier,
    AVG("multiplier") as avg_multiplier
FROM "AviatorRound";
