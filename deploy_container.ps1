# Deploy Container App to Azure
# Get credentials from: az acr credential show --resource-group aviator-rg --name aviatorai
$username = "aviatorai"
$password = "<YOUR-ACR-PASSWORD>"  # Get from: az acr credential show
$supabaseUrl = "<YOUR-SUPABASE-URL>"
$supabaseKey = "<YOUR-SUPABASE-KEY>"

Write-Host "Creating Container App..." -ForegroundColor Cyan

az containerapp create `
  --name aviator-ai-foundry `
  --resource-group aviator-rg `
  --environment aviator-env `
  --image aviatorai.azurecr.io/aviator-foundry:v1.0 `
  --target-port 8000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --cpu 2 `
  --memory 4Gi `
  --registry-server aviatorai.azurecr.io `
  --registry-username $username `
  --registry-password $password `
  --env-vars SUPABASE_URL=$supabaseUrl SUPABASE_KEY=$supabaseKey LOG_LEVEL="INFO" WORKERS="4"

Write-Host "Container App creation initiated!" -ForegroundColor Green
Write-Host "Waiting for deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Getting Container App URL..." -ForegroundColor Cyan
$appUrl = az containerapp show --resource-group aviator-rg --name aviator-ai-foundry --query properties.configuration.ingress.fqdn -o tsv

Write-Host "Container App URL: https://$appUrl" -ForegroundColor Green
Write-Host "Waiting 2-3 minutes for service to start..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Write-Host "Health check attempt $attempt/$maxAttempts..." -ForegroundColor Gray

    try {
        $response = Invoke-WebRequest -Uri "https://$appUrl/health" -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "Service is ready!" -ForegroundColor Green
            $ready = $true
        }
    } catch {
        Write-Host "  Waiting..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if ($ready) {
    Write-Host "Testing /health endpoint..." -ForegroundColor Cyan
    $health = Invoke-RestMethod -Uri "https://$appUrl/health"
    Write-Host "Status: $($health.status)" -ForegroundColor Green
    Write-Host "Models Loaded: $($health.models_loaded)/15" -ForegroundColor Green
}

Write-Host "`nDone! Update your .env file with:" -ForegroundColor Green
Write-Host "AZURE_FOUNDRY_ENDPOINT=https://$appUrl" -ForegroundColor Yellow
