-- SQL script to create the Predictions table in Supabase
-- Run this in your Supabase SQL Editor

-- Create AviatorPredictions table
CREATE TABLE IF NOT EXISTS "AviatorPredictions" (
    "predictionId" BIGSERIAL PRIMARY KEY,
    "predictedMultiplier" REAL NOT NULL,
    "actualMultiplier" REAL DEFAULT NULL,
    "predictionError" REAL DEFAULT NULL,
    "confidence" REAL NOT NULL,
    "modelType" VARCHAR(50) NOT NULL DEFAULT 'RandomForest',
    "trainingSamples" INTEGER NOT NULL,
    "predictionTimestamp" TIMESTAMP NOT NULL DEFAULT NOW(),
    "actualTimestamp" TIMESTAMP DEFAULT NULL,
    "roundNumber" INTEGER,
    "features" JSONB DEFAULT NULL,
    "created_at" TIMESTAMP DEFAULT NOW()
);

-- Create index on predictionTimestamp for faster queries
CREATE INDEX IF NOT EXISTS idx_prediction_timestamp
ON "AviatorPredictions" ("predictionTimestamp");

-- Create index on actualTimestamp for filtering completed predictions
CREATE INDEX IF NOT EXISTS idx_actual_timestamp
ON "AviatorPredictions" ("actualTimestamp");

-- Add comment to table
COMMENT ON TABLE "AviatorPredictions" IS 'Stores ML predictions for crash multipliers and their accuracy';

-- Column comments
COMMENT ON COLUMN "AviatorPredictions"."predictionId" IS 'Auto-incrementing primary key';
COMMENT ON COLUMN "AviatorPredictions"."predictedMultiplier" IS 'Predicted crash multiplier value';
COMMENT ON COLUMN "AviatorPredictions"."actualMultiplier" IS 'Actual crash multiplier (filled after round completes)';
COMMENT ON COLUMN "AviatorPredictions"."predictionError" IS 'Absolute error: |predicted - actual|';
COMMENT ON COLUMN "AviatorPredictions"."confidence" IS 'Model confidence score (0-1)';
COMMENT ON COLUMN "AviatorPredictions"."modelType" IS 'Type of ML model used (RandomForest, XGBoost, etc)';
COMMENT ON COLUMN "AviatorPredictions"."trainingSamples" IS 'Number of historical rounds used for training';
COMMENT ON COLUMN "AviatorPredictions"."predictionTimestamp" IS 'When prediction was made';
COMMENT ON COLUMN "AviatorPredictions"."actualTimestamp" IS 'When actual result occurred';
COMMENT ON COLUMN "AviatorPredictions"."roundNumber" IS 'Round number this prediction is for';
COMMENT ON COLUMN "AviatorPredictions"."features" IS 'Optional JSON with feature values used';

-- Optional: Create a view for prediction accuracy analysis
CREATE OR REPLACE VIEW "PredictionAccuracy" AS
SELECT
    "modelType",
    COUNT(*) as total_predictions,
    COUNT("actualMultiplier") as completed_predictions,
    AVG("predictionError") as avg_error,
    MIN("predictionError") as min_error,
    MAX("predictionError") as max_error,
    AVG("confidence") as avg_confidence,
    AVG(ABS("predictedMultiplier" - "actualMultiplier")) as mae
FROM "AviatorPredictions"
WHERE "actualMultiplier" IS NOT NULL
GROUP BY "modelType";

-- Optional: Function to update prediction with actual result
CREATE OR REPLACE FUNCTION update_prediction_result(
    pred_id BIGINT,
    actual_mult REAL,
    actual_time TIMESTAMP
)
RETURNS VOID AS $$
BEGIN
    UPDATE "AviatorPredictions"
    SET
        "actualMultiplier" = actual_mult,
        "actualTimestamp" = actual_time,
        "predictionError" = ABS("predictedMultiplier" - actual_mult)
    WHERE "predictionId" = pred_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_prediction_result IS 'Updates a prediction with actual results and calculates error';
