# Azure AI Foundry Service - Deployment Steps

## Current Issue

The Azure service is running but **cannot save to `analytics_round_signals`** table because:
- ✅ Service receives requests from bot
- ✅ Runs 15 AutoML models
- ❌ **Missing Supabase credentials** - cannot insert analytics signal
- Returns `signal_id=None`

## Solution: Redeploy with Supabase Credentials

### Option 1: Set Environment Variables in Azure Portal

1. Go to **Azure Portal** → Your Container App
2. Navigate to **Settings** → **Environment Variables**
3. Add these variables:
   ```
   SUPABASE_URL=https://zofojiubrykbtmstfhzx.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s
   ```
4. **Restart** the container app
5. Test with a new round

### Option 2: Redeploy with Updated Docker Image

1. **Build new Docker image** with .env file:
   ```bash
   cd azure_foundry_service
   docker build -t aviator-foundry:latest .
   ```

2. **Push to Azure Container Registry**:
   ```bash
   # Tag image
   docker tag aviator-foundry:latest <your-registry>.azurecr.io/aviator-foundry:latest

   # Push
   docker push <your-registry>.azurecr.io/aviator-foundry:latest
   ```

3. **Update Container App** to use new image

4. **Verify deployment**:
   ```bash
   curl https://aviator-ai-foundry.kindmeadow-9ed26673.eastus.azurecontainerapps.io/health
   ```

## Expected Result After Fix

```
[01:30:45] INFO: Requesting prediction from Azure AI Foundry...
[01:30:45] ✓ Azure prediction received
[01:30:45]   - Models: 15/15  ← Should be 15, not 0
[01:30:45]   - Confidence: 67%  ← Should have confidence
[01:30:45] SUCCESS: Azure AI Foundry prediction completed
```

And you should see entries in **`analytics_round_signals`** table with:
- `round_id`: The roundId from AviatorRound
- `signal_type`: BULLISH/BEARISH/NEUTRAL
- `confidence_score`: 0.0-1.0
- `payload`: Full 15-model predictions in JSON

## Verification Steps

1. **Check Azure Logs**:
   ```bash
   # You should see:
   [TIME] INFO: Supabase connected successfully
   [TIME] INFO: Signal inserted (ID: 123, Type: BULLISH, Confidence: 67%)
   ```

2. **Query Supabase**:
   ```sql
   SELECT * FROM analytics_round_signals
   ORDER BY created_at DESC
   LIMIT 10;
   ```

3. **Test API**:
   ```bash
   curl -X POST https://your-endpoint/predict \
     -H "Content-Type: application/json" \
     -d '{"round_id": 1, "round_number": 1}'
   ```

## Files Updated in This Branch

- `azure_foundry_service/app.py` - Fixed Pydantic models
- `azure_foundry_service/.env` - Added Supabase credentials
- `azure_foundry_client.py` - Improved error handling
- `main.py` - Commented out local ML predictions

## Current Branch Status

```bash
git branch  # Should show: * observer-v2
git log --oneline -5
```

All changes are committed and ready for deployment!
