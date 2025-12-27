-- Diagnostic SQL for AviatorRound Table Issues
-- Run this in Supabase SQL Editor to understand the problem

-- =============================================================================
-- STEP 1: Check if table exists
-- =============================================================================
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'AviatorRound'
) AS table_exists;

-- =============================================================================
-- STEP 2: View table structure (all columns)
-- =============================================================================
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'AviatorRound'
ORDER BY ordinal_position;

-- =============================================================================
-- STEP 3: Find ALL triggers on the table
-- =============================================================================
SELECT
    tgname AS trigger_name,
    tgenabled AS is_enabled,
    pg_get_triggerdef(oid) AS trigger_definition
FROM pg_trigger
WHERE tgrelid = '"AviatorRound"'::regclass
AND tgisinternal = false;  -- Exclude internal triggers

-- =============================================================================
-- STEP 4: Find functions that might be called by triggers
-- =============================================================================
SELECT
    p.proname AS function_name,
    pg_get_functiondef(p.oid) AS function_definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND (
    pg_get_functiondef(p.oid) LIKE '%AviatorRound%'
    OR pg_get_functiondef(p.oid) LIKE '%m_std%'
);

-- =============================================================================
-- STEP 5: Check RLS (Row Level Security) policies
-- =============================================================================
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'AviatorRound';

-- =============================================================================
-- STEP 6: Check current data (if any)
-- =============================================================================
SELECT
    COUNT(*) as total_rows,
    MIN("timestamp") as earliest_round,
    MAX("timestamp") as latest_round,
    MIN("multiplier") as min_multiplier,
    MAX("multiplier") as max_multiplier,
    AVG("multiplier") as avg_multiplier
FROM "AviatorRound";

-- =============================================================================
-- STEP 7: View sample data
-- =============================================================================
SELECT *
FROM "AviatorRound"
ORDER BY "timestamp" DESC
LIMIT 5;

-- =============================================================================
-- STEP 8: Test a simple INSERT (will fail if triggers are problematic)
-- =============================================================================
DO $$
DECLARE
    test_round_id BIGINT := 99999999999999;
    error_message TEXT;
BEGIN
    BEGIN
        -- Try to insert test data
        INSERT INTO "AviatorRound" ("roundId", "multiplier", "timestamp")
        VALUES (test_round_id, 2.50, NOW());

        RAISE NOTICE '✅ TEST INSERT SUCCESSFUL! Table is working correctly.';

        -- Clean up test data
        DELETE FROM "AviatorRound" WHERE "roundId" = test_round_id;

    EXCEPTION
        WHEN OTHERS THEN
            error_message := SQLERRM;
            RAISE NOTICE '❌ TEST INSERT FAILED!';
            RAISE NOTICE 'Error: %', error_message;

            -- Try to clean up anyway
            BEGIN
                DELETE FROM "AviatorRound" WHERE "roundId" = test_round_id;
            EXCEPTION
                WHEN OTHERS THEN
                    -- Ignore cleanup errors
            END;
    END;
END $$;

-- =============================================================================
-- RESULTS INTERPRETATION
-- =============================================================================

/*
WHAT TO LOOK FOR:

1. TABLE STRUCTURE (Step 2):
   - Should have: roundId, multiplier, timestamp
   - Should NOT have: m_std, m_mean, or other calculated columns
   - If you see extra columns → they might be causing issues

2. TRIGGERS (Step 3):
   - If you see ANY triggers → check their definitions
   - Look for references to "m_std" or other missing columns
   - Solution: DROP those triggers

3. FUNCTIONS (Step 4):
   - If functions reference "m_std" → they're the problem
   - Solution: DROP the trigger that calls these functions

4. TEST INSERT (Step 8):
   - ✅ Success → Your table is fine!
   - ❌ Failed → Look at the error message for clues

COMMON ERROR PATTERNS:

Error: "column m_std does not exist"
→ A trigger is trying to calculate statistics
→ Solution: Drop the trigger

Error: "permission denied"
→ RLS policy is blocking inserts
→ Solution: ALTER TABLE "AviatorRound" DISABLE ROW LEVEL SECURITY;

Error: "duplicate key"
→ roundId already exists
→ This is normal for test data, not an issue
*/
