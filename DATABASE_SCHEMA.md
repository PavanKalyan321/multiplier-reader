# Database Schema Reference

## analytics_round_signals Table

This table stores ML prediction signals and analytics data for each round.

### Table Definition

```sql
create table public.analytics_round_signals (
  id bigserial not null,
  round_id bigint not null,
  multiplier numeric not null,
  model_name text not null,
  model_output jsonb not null,
  confidence numeric null,
  metadata jsonb null default '{}'::jsonb,
  created_at timestamp with time zone null default now(),
  payload text null,
  constraint analytics_round_signals_pkey primary key (id)
) TABLESPACE pg_default;
```

### Indexes

```sql
-- Index on round_id for fast lookups by round
create index IF not exists idx_analytics_round_signals_round_id
  on public.analytics_round_signals using btree (round_id) TABLESPACE pg_default;

-- Unique constraint ensuring one signal per round per model
create unique INDEX IF not exists ux_round_model
  on public.analytics_round_signals using btree (round_id, model_name) TABLESPACE pg_default;

-- Composite index for model-specific time-series queries
create index IF not exists idx_analytics_round_signals_model_name_created_at
  on public.analytics_round_signals using btree (model_name, created_at) TABLESPACE pg_default;
```

### Column Descriptions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | bigserial | NOT NULL | Primary key, auto-incrementing |
| `round_id` | bigint | NOT NULL | Foreign key to AviatorRound table |
| `multiplier` | numeric | NOT NULL | Actual multiplier from the round |
| `model_name` | text | NOT NULL | Name of the ML model (e.g., 'RandomForest', 'MultiModel', 'AdvancedMultiModel') |
| `model_output` | jsonb | NOT NULL | JSON object containing model-specific output data |
| `confidence` | numeric | NULL | Model confidence score (0-1) |
| `metadata` | jsonb | NULL | Additional metadata (defaults to empty JSON object) |
| `created_at` | timestamp with time zone | NULL | Timestamp of signal creation (defaults to now()) |
| `payload` | text | NULL | JSON string containing full prediction details |

### Usage Examples

**Single Model Signal:**
- `model_name`: "RandomForest"
- `model_output`: `{"predicted_multiplier": 2.5, "features_used": 21}`
- `payload`: JSON with prediction details
- **Note:** All float values rounded to 1 decimal place in payload

**Multi-Model Signal:**
- `model_name`: "MultiModel"
- `model_output`: `{"num_models": 5, "models": ["RandomForest", "GradientBoosting", ...]}`
- `payload`: JSON with all model predictions
- **Note:** All float values rounded to 1 decimal place in payload

**Advanced Multi-Model Signal:**
- `model_name`: "AdvancedMultiModel"
- `model_output`: `{"version": "advanced_v1", "total_models": 25, "model_groups": {...}}`
- `payload`: JSON with ensemble, hybrid strategy, all predictions, and patterns
- **Note:** All float values recursively rounded to 1 decimal place in payload

### Data Formatting

All numeric values in the `payload` JSON are automatically rounded to **1 decimal place** for:
- Multiplier predictions (e.g., `3.5234567` → `3.5`)
- Confidence scores (e.g., `0.67890123` → `0.7`)
- Prediction ranges (e.g., `[2.8234567, 4.2234567]` → `[2.8, 4.2]`)

This ensures clean, readable data storage and reduces payload size.

### Unique Constraint

The `ux_round_model` index ensures that only one signal per model per round can exist. This prevents duplicate predictions for the same round.
