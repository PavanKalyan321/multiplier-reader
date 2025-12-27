-- Fix the analytics_generate_round_signal trigger
-- Run this in Supabase SQL Editor

-- Step 1: Check the current trigger function
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'analytics_generate_round_signal';

-- Step 2: Drop and recreate the function WITHOUT referencing m_std
-- This is a placeholder - you'll need to adjust based on what you want the trigger to do

CREATE OR REPLACE FUNCTION analytics_generate_round_signal()
RETURNS TRIGGER AS $$
BEGIN
    -- Option A: Do nothing (just return the new row)
    -- Use this if you don't need the trigger at all
    RETURN NEW;

    -- Option B: Add your custom logic here
    -- Example: Log to another table, calculate stats, etc.
    -- But make sure NOT to reference any columns that don't exist (like m_std)

    /*
    -- Example: Insert into a stats table
    INSERT INTO round_stats (round_id, multiplier, timestamp)
    VALUES (NEW."roundId", NEW.multiplier, NEW.timestamp);
    */

END;
$$ LANGUAGE plpgsql;

-- Step 3: Verify the trigger is still enabled
SELECT
    tgname as trigger_name,
    tgenabled as is_enabled,
    pg_get_triggerdef(oid) as definition
FROM pg_trigger
WHERE tgrelid = '"AviatorRound"'::regclass;

-- Step 4: Test insert
DO $$
DECLARE
    test_id BIGINT;
BEGIN
    -- Insert test data
    INSERT INTO "AviatorRound" (multiplier, timestamp)
    VALUES (2.50, NOW())
    RETURNING "roundId" INTO test_id;

    RAISE NOTICE '✅ Test insert successful! Round ID: %', test_id;

    -- Clean up
    DELETE FROM "AviatorRound" WHERE "roundId" = test_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '❌ Test insert failed: %', SQLERRM;
END $$;

-- Alternative: Disable the trigger completely (if you don't need it)
-- ALTER TABLE "AviatorRound" DISABLE TRIGGER after_insert_analytics_generate;
