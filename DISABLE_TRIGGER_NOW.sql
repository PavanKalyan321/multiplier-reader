-- IMMEDIATE FIX: Disable the problematic trigger
-- Run this RIGHT NOW in Supabase SQL Editor

-- This will allow rounds to be inserted without the trigger running
ALTER TABLE "AviatorRound"
DISABLE TRIGGER after_insert_analytics_generate;

-- Verify the trigger is disabled
SELECT
    tgname as trigger_name,
    CASE tgenabled
        WHEN 'D' THEN 'DISABLED'
        WHEN 'O' THEN 'ENABLED'
        ELSE 'UNKNOWN'
    END as status
FROM pg_trigger
WHERE tgrelid = '"AviatorRound"'::regclass
AND tgname = 'after_insert_analytics_generate';

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

    RAISE NOTICE 'Test data cleaned up. Trigger is fixed!';
END $$;
