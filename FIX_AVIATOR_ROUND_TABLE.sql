-- SQL Script to Fix AviatorRound Table
-- Run this in your Supabase SQL Editor

-- Step 1: Check existing triggers
SELECT
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'AviatorRound';

-- Step 2: Drop any problematic triggers
-- (Uncomment if you see triggers referencing m_std in Step 1)
-- DROP TRIGGER IF EXISTS trigger_name_here ON "AviatorRound";

-- Step 3: Check table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'AviatorRound'
ORDER BY ordinal_position;

-- Step 4: Drop and recreate table (CLEAN SLATE)
-- WARNING: This will DELETE all existing data!
-- Comment out if you want to keep existing data

DROP TABLE IF EXISTS "AviatorRound" CASCADE;

CREATE TABLE "AviatorRound" (
    "roundId" BIGINT PRIMARY KEY,
    "multiplier" REAL NOT NULL,
    "timestamp" TIMESTAMP DEFAULT NOW(),
    "created_at" TIMESTAMP DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_aviator_round_timestamp
ON "AviatorRound" ("timestamp" DESC);

-- Add helpful comment
COMMENT ON TABLE "AviatorRound" IS 'Stores completed game rounds with crash multipliers';
COMMENT ON COLUMN "AviatorRound"."roundId" IS 'Unique ID generated from timestamp (YYYYMMDDHHMMSSmmm)';
COMMENT ON COLUMN "AviatorRound"."multiplier" IS 'Final crash multiplier value';
COMMENT ON COLUMN "AviatorRound"."timestamp" IS 'When the round ended';

-- Verify table structure
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'AviatorRound'
ORDER BY ordinal_position;

-- Test insert
INSERT INTO "AviatorRound" ("roundId", "multiplier", "timestamp")
VALUES (20251224100000000, 2.50, NOW());

-- Verify insert worked
SELECT * FROM "AviatorRound" ORDER BY "timestamp" DESC LIMIT 5;

-- Clean up test data
DELETE FROM "AviatorRound" WHERE "roundId" = 20251224100000000;
