# Observer Module v1.0.0

## Overview

The Observer Module is a stable, production-ready system for tracking and predicting game multipliers using Machine Learning and real-time data collection.

## Branch & Version Info

- **Branch**: `observer-v1`
- **Tag**: `observer-v1.0.0`
- **Status**: Stable Release
- **Repository**: https://github.com/PavanKalyan321/multiplier-reader

## Core Features

### 1. Real-time Multiplier Tracking
- OCR-based screen capture for game multiplier reading
- Automatic round detection and tracking
- Complete round history with statistics

### 2. ML Prediction System
- **Algorithm**: Random Forest Regressor
- **Features**: 21 engineered features including:
  - Statistical (mean, std, min, max, median)
  - Duration metrics
  - Trend analysis
  - Recent patterns
  - Streak detection
  - Time-based features
- **Training**: Adaptive lookback windows (starts after 5 rounds)
- **Output**: Predicted multiplier with confidence score and range

### 3. Two-Table Supabase Architecture

#### Table 1: `AviatorRound`
Stores actual game results:
```sql
- roundId (auto-generated IDENTITY)
- multiplier (actual crash multiplier)
- timestamp (when the round ended)
```

#### Table 2: `analytics_round_signals`
Stores predictions with payload structure:
```sql
- id (signal ID)
- round_id (foreign key to AviatorRound)
- multiplier (actual multiplier from that round)
- model_name (e.g., "RandomForest")
- model_output (JSONB with model details)
- confidence (0-1 probability)
- metadata (JSONB with additional info)
- payload (TEXT/JSON with prediction structure)
- created_at (timestamp, synced with round)
```

### 4. Payload Structure

The `payload` column contains prediction details in JSON format:

```json
{
  "modelName": "RandomForest",
  "id": 401,
  "expectedOutput": 3.15,
  "confidence": "73%",
  "range": "2.52-3.78"
}
```

**Key Points**:
- `multiplier` column: Stores **actual** multiplier from the round
- `payload` column: Stores **prediction** for the next round
- Range: ±20% of predicted value
- Timestamp: Synchronized between both tables

## Data Flow

```
Round N completes (multiplier: 2.45x)
    ↓
Save to AviatorRound
    → roundId: 401
    → multiplier: 2.45
    → timestamp: T
    ↓
ML Model makes prediction for Round N+1
    → predicted: 3.15x
    → confidence: 73%
    → range: 2.52-3.78
    ↓
Save to analytics_round_signals
    → round_id: 401
    → multiplier: 2.45 (actual from round 401)
    → payload: {prediction for round 402}
    → created_at: T (same timestamp)
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Tesseract OCR (Windows)
- Supabase account and credentials

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure
Update `multiplier_config.json` with your settings:
- Screen capture region
- OCR parameters
- Supabase credentials (URL and Key)

### Run
```bash
python main.py
```

## File Structure

### Core Modules
- `main.py` - Main application loop with ML integration
- `multiplier_reader.py` - OCR and screen capture
- `game_tracker.py` - Round detection and tracking
- `ml_predictor.py` - Random Forest prediction engine
- `supabase_client.py` - Database operations
- `screen_capture.py` - Screen region capture utilities
- `config.py` - Configuration management

### Documentation
- `NEW_PAYLOAD_STRUCTURE.md` - Payload format documentation
- `IMPLEMENTATION_COMPLETE.md` - Implementation details
- `TIMESTAMP_SYNC_COMPLETE.md` - Timestamp synchronization
- `ML_PREDICTION_GUIDE.md` - ML system overview
- `TWO_TABLE_FLOW.md` - Database architecture

### Test Suite
- `test_new_payload_structure.py` - Payload structure verification
- `test_same_timestamp.py` - Timestamp sync test
- `test_multi_round_flow.py` - Multi-round simulation
- `test_complete_flow.py` - End-to-end test
- `test_insert_round.py` - Round insertion test
- `test_insert_prediction.py` - Prediction insertion test
- `test_5_round_prediction.py` - 5-round minimum test

## Database Queries

### View All Predictions
```sql
SELECT
    ar."roundId",
    ar.multiplier as actual_multiplier,
    ar.timestamp,
    ars.id as signal_id,
    ars.multiplier as stored_actual,
    ars.payload::json->>'expectedOutput' as predicted_next,
    ars.payload::json->>'confidence' as confidence,
    ars.payload::json->>'range' as prediction_range,
    ars.created_at
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId"
ORDER BY ar."roundId" DESC;
```

### Check Timestamp Sync
```sql
SELECT
    ar."roundId",
    ar.timestamp as round_timestamp,
    ars.created_at as signal_timestamp,
    CASE
        WHEN ar.timestamp = ars.created_at THEN 'MATCH'
        ELSE 'DIFFERENT'
    END as timestamp_match
FROM "AviatorRound" ar
JOIN analytics_round_signals ars ON ars.round_id = ar."roundId";
```

### Compare Predictions vs Actuals
```sql
SELECT
    ars.round_id,
    ars.multiplier as previous_round_actual,
    ars.payload::json->>'expectedOutput' as predicted_for_next,
    next_round.multiplier as next_round_actual,
    ABS(
        (ars.payload::json->>'expectedOutput')::numeric -
        next_round.multiplier
    ) as prediction_error
FROM analytics_round_signals ars
JOIN "AviatorRound" current_round ON current_round."roundId" = ars.round_id
LEFT JOIN LATERAL (
    SELECT multiplier
    FROM "AviatorRound"
    WHERE timestamp > current_round.timestamp
    ORDER BY timestamp ASC
    LIMIT 1
) next_round ON true;
```

## Technical Specifications

### ML Model
- **Type**: Random Forest Regressor
- **Trees**: 100
- **Features**: 21 engineered features
- **Min Training Samples**: 5 rounds
- **Lookback Window**: Adaptive (4-5 rounds)
- **Retraining**: Every 10 rounds

### Prediction Range
- Calculated as ±20% of predicted value
- Minimum value capped at 1.0x
- Format: "min-max" (e.g., "2.52-3.78")

### Timestamp Synchronization
- Both tables use the exact same timestamp
- Format: ISO 8601 with timezone
- Source: Round end time from game tracker

## API Reference

### SupabaseLogger.insert_analytics_signal()
```python
def insert_analytics_signal(
    round_id: int,
    actual_multiplier: float,
    predicted_multiplier: float,
    model_name: str,
    confidence: float,
    prediction_range: tuple,
    model_output: dict = None,
    metadata: dict = None,
    timestamp: datetime = None
) -> int
```

**Parameters**:
- `actual_multiplier`: Actual from the round that just ended
- `predicted_multiplier`: Prediction for the next round
- `prediction_range`: Tuple of (min, max) values
- `timestamp`: Must match the round's timestamp

**Returns**: Signal ID if successful, None otherwise

## Version History

### v1.0.0 (2025-12-24)
- Initial stable release
- ML prediction system with Random Forest
- Two-table Supabase architecture
- Payload structure implementation
- Timestamp synchronization
- Comprehensive test suite
- Complete documentation

## Contributing

This is a stable module. To make changes:
1. Create a new branch from `observer-v1`
2. Make your changes
3. Test thoroughly using the test suite
4. Submit a pull request

## License

Internal project - All rights reserved

## Support

For issues or questions:
- Check the documentation files
- Run the test suite to verify functionality
- Review the verification queries in Supabase

## Acknowledgments

Built with Claude Code (Anthropic)
Co-Authored-By: Claude Sonnet 4.5

---

**Last Updated**: 2025-12-24
**Branch**: observer-v1
**Tag**: observer-v1.0.0
**Status**: ✅ Stable & Production Ready
