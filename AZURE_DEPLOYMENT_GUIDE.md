# Azure AI Foundry Deployment Guide

## Overview
This guide walks you through deploying the Azure AI Foundry service to Microsoft Azure using Container Apps.

## Prerequisites

1. **Azure Account** - Active Azure subscription
2. **Azure CLI** - Installed and configured
3. **Docker** - Installed locally (for testing)
4. **Git** - For version control
5. **Supabase Credentials** - URL and API key ready

## Architecture

```
Bot (main.py)
    ↓
Azure Foundry Client (azure_foundry_client.py)
    ↓
Azure Container App (FastAPI service)
    ↓
Supabase (AviatorRound + analytics_round_signals)
```

## Step 1: Prepare Local Environment

### 1.1 Create .env file
```bash
cd azure_foundry_service
cp .env.example .env
```

### 1.2 Edit .env with your credentials
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 1.3 Test locally with Docker
```bash
# Build image
docker build -t aviator-foundry:latest .

# Run container
docker run -p 8000:8000 \
  -e SUPABASE_URL="https://your-project.supabase.co" \
  -e SUPABASE_KEY="your-key" \
  aviator-foundry:latest

# Test endpoint
curl http://localhost:8000/health
```

## Step 2: Create Azure Resources

### 2.1 Create Resource Group
```bash
az group create \
  --name aviator-rg \
  --location eastus
```

### 2.2 Create Container Registry
```bash
# Create ACR
az acr create \
  --resource-group aviator-rg \
  --name aviatorai \
  --sku Basic

# Get login credentials
az acr login --name aviatorai
```

### 2.3 Create Container App Environment
```bash
# Create environment
az containerapp env create \
  --name aviator-env \
  --resource-group aviator-rg \
  --location eastus
```

## Step 3: Build and Push Image

### 3.1 Build Docker image
```bash
# Navigate to azure_foundry_service directory
cd azure_foundry_service

# Build image with ACR
az acr build \
  --registry aviatorai \
  --image aviator-foundry:v1.0 \
  .
```

### 3.2 Verify image in registry
```bash
az acr repository list --name aviatorai
```

## Step 4: Create Container App

### 4.1 Create the Container App
```bash
az containerapp create \
  --name aviator-ai-foundry \
  --resource-group aviator-rg \
  --environment aviator-env \
  --image aviatorai.azurecr.io/aviator-foundry:v1.0 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 2 \
  --memory 4Gi \
  --registry-server aviatorai.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --env-vars \
    SUPABASE_URL="https://your-project.supabase.co" \
    SUPABASE_KEY="your-key" \
    LOG_LEVEL="INFO" \
    WORKERS="4"
```

### 4.2 Get the Container App URL
```bash
az containerapp show \
  --resource-group aviator-rg \
  --name aviator-ai-foundry \
  --query properties.configuration.ingress.fqdn
```

Output will be like: `aviator-ai-foundry.kindlydesert-abc123.eastus.azurecontainerapps.io`

## Step 5: Configure Bot

### 5.1 Update bot .env file
Add to your bot's .env file:

```env
AZURE_FOUNDRY_ENDPOINT=https://aviator-ai-foundry.kindlydesert-abc123.eastus.azurecontainerapps.io
AZURE_FOUNDRY_API_KEY=optional-for-now
```

### 5.2 Verify bot can reach Azure service
```bash
curl https://aviator-ai-foundry.kindlydesert-abc123.eastus.azurecontainerapps.io/health
```

Should return:
```json
{
  "status": "healthy",
  "models_loaded": 15,
  "supabase_connected": true,
  "timestamp": "2025-01-07T10:30:00.123456"
}
```

## Step 6: Monitoring and Management

### 6.1 View logs
```bash
az containerapp logs show \
  --name aviator-ai-foundry \
  --resource-group aviator-rg \
  --follow
```

### 6.2 Get container app details
```bash
az containerapp show \
  --name aviator-ai-foundry \
  --resource-group aviator-rg
```

### 6.3 Update image (after code changes)
```bash
# Build new image
az acr build \
  --registry aviatorai \
  --image aviator-foundry:v1.1 \
  ./azure_foundry_service

# Update container app
az containerapp update \
  --name aviator-ai-foundry \
  --resource-group aviator-rg \
  --image aviatorai.azurecr.io/aviator-foundry:v1.1
```

## Step 7: Scaling and Performance

### 7.1 Auto-scaling configuration
```bash
az containerapp update \
  --name aviator-ai-foundry \
  --resource-group aviator-rg \
  --min-replicas 1 \
  --max-replicas 5 \
  --cpu 2 \
  --memory 4Gi
```

### 7.2 Monitor performance
```bash
az monitor metrics list \
  --resource aviator-ai-foundry \
  --resource-group aviator-rg \
  --metric "Requests"
```

## Step 8: Cost Estimation

### 8.1 Resource costs
- **Container Registry (Basic)**: ~$5/month
- **Container App**: ~$40-80/month (1-3 replicas, 2 vCPU, 4GB RAM)
- **Monitoring**: ~$5/month (optional)
- **Total**: ~$50-90/month

### 8.2 Cost optimization
- Use spot instances for dev/test
- Set appropriate scaling limits
- Monitor memory usage
- Clean up unused resources

## Troubleshooting

### Issue: Container won't start
```bash
# Check logs
az containerapp logs show --follow

# Common causes:
# 1. Missing environment variables
# 2. Port already in use
# 3. Dependency installation failed
```

### Issue: Can't connect to Supabase
```bash
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection manually
python3 -c "from supabase import create_client; c = create_client(url, key); print('Connected')"
```

### Issue: Predictions timing out
- Increase CPU/memory allocation
- Check model loading time
- Verify network connectivity
- Check Supabase query performance

## Rollback Procedure

If something goes wrong:

```bash
# Revert to previous image version
az containerapp update \
  --name aviator-ai-foundry \
  --resource-group aviator-rg \
  --image aviatorai.azurecr.io/aviator-foundry:v1.0
```

## Security Best Practices

1. **Use Azure Key Vault** for secrets
```bash
az keyvault create \
  --name aviator-kv \
  --resource-group aviator-rg

az keyvault secret set \
  --vault-name aviator-kv \
  --name supabase-key \
  --value "your-key"
```

2. **Enable authentication** on Container App (when API key added)

3. **Use managed identities** for secure resource access

4. **Enable logging** to Azure Monitor

## Testing Endpoints

### Health Check
```bash
curl https://aviator-ai-foundry.xxx.azurecontainerapps.io/health
```

### List Models
```bash
curl https://aviator-ai-foundry.xxx.azurecontainerapps.io/models
```

### Get Status
```bash
curl https://aviator-ai-foundry.xxx.azurecontainerapps.io/status
```

### Make Prediction
```bash
curl -X POST https://aviator-ai-foundry.xxx.azurecontainerapps.io/predict \
  -H "Content-Type: application/json" \
  -d '{"round_id": 123, "round_number": 456}'
```

## Next Steps

1. ✅ Deploy Azure Container App
2. ✅ Update bot configuration
3. ✅ Test bot-to-Azure communication
4. ⚪ Implement actual AutoML models (Phase 2)
5. ⚪ Set up monitoring and alerts
6. ⚪ Configure auto-scaling policies
7. ⚪ Add Azure DevOps CI/CD pipeline

## Support

For issues or questions:
1. Check Azure Portal logs
2. Review container app metrics
3. Test endpoints manually
4. Check Supabase table permissions
5. Review bot logs for API errors

## Quick Reference

```bash
# Most common commands

# Deploy new version
az acr build --registry aviatorai --image aviator-foundry:v1.1 ./azure_foundry_service
az containerapp update --name aviator-ai-foundry --resource-group aviator-rg --image aviatorai.azurecr.io/aviator-foundry:v1.1

# Check logs
az containerapp logs show --name aviator-ai-foundry --resource-group aviator-rg --follow

# Get URL
az containerapp show --name aviator-ai-foundry --resource-group aviator-rg --query properties.configuration.ingress.fqdn

# Test health
curl https://aviator-ai-foundry.xxx.azurecontainerapps.io/health

# Scale up
az containerapp update --name aviator-ai-foundry --resource-group aviator-rg --max-replicas 5

# Check costs
az billing statement list --resource-group aviator-rg
```
