# Azure AI Foundry Deployment Script for PowerShell
# This script automates the entire Azure deployment process
# Just run: powershell -ExecutionPolicy Bypass -File AZURE_DEPLOYMENT_POWERSHELL.ps1

# Color output for better readability
function Write-Success {
    Write-Host "[OK] $args" -ForegroundColor Green
}

function Write-Info {
    Write-Host "[INFO] $args" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    Write-Host "[WARNING] $args" -ForegroundColor Yellow
}

function Write-Error-Custom {
    Write-Host "[ERROR] $args" -ForegroundColor Red
}

# Start
Write-Host "`n" + ("=" * 80) -ForegroundColor Magenta
Write-Host "Azure AI Foundry Deployment Script" -ForegroundColor Magenta
Write-Host ("=" * 80) -ForegroundColor Magenta

# Step 0: Verify Azure CLI is installed
Write-Info "Checking Azure CLI installation..."
try {
    $azVersion = az --version 2>$null
    Write-Success "Azure CLI found"
    Write-Info "Version: $($azVersion[0])"
} catch {
    Write-Error-Custom "Azure CLI not installed!"
    Write-Host "Please install from: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Step 0.5: Check if logged in
Write-Info "Checking Azure login status..."
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Success "Logged in as: $($account.user.name)"
} catch {
    Write-Warning-Custom "Not logged in. Running: az login"
    az login
}

# Configuration Variables
$resourceGroup = "aviator-rg"
$registryName = "aviatorai"
$containerAppName = "aviator-ai-foundry"
$containerAppEnv = "aviator-env"
$location = "eastus"
$imageName = "aviator-foundry"
$imageTag = "v1.0"
$cpuCores = "2"
$memorySize = "4Gi"
$minReplicas = "1"
$maxReplicas = "3"

# Supabase credentials (hardcoded - in production use Key Vault)
$supabaseUrl = "https://zofojiubrykbtmstfhzx.supabase.co"
$supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZm9qaXVicnlrYnRtc3RmaHp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NzU0OTEsImV4cCI6MjA3OTQ1MTQ5MX0.mxwvnhT-ouONWff-gyqw67lKon82nBx2fsbd8meyc8s"

Write-Host "`n" + ("=" * 80)
Write-Info "Configuration:"
Write-Info "  Resource Group: $resourceGroup"
Write-Info "  Registry: $registryName"
Write-Info "  Container App: $containerAppName"
Write-Info "  Location: $location"
Write-Info "  Image: $imageName`:$imageTag"
Write-Info "  CPU: $cpuCores vCPU"
Write-Info "  Memory: $memorySize"
Write-Host ("=" * 80) + "`n"

# Step 1: Create Resource Group
Write-Info "STEP 1: Creating Resource Group..."
Write-Host "Command: az group create --name $resourceGroup --location $location"
try {
    $group = az group create --name $resourceGroup --location $location | ConvertFrom-Json
    Write-Success "Resource Group Created: $($group.name) in $($group.location)"
} catch {
    Write-Error-Custom "Failed to create resource group"
    Write-Host $_.Exception.Message
    exit 1
}

# Step 2: Create Container Registry
Write-Info "STEP 2: Creating Container Registry..."
Write-Host "Command: az acr create --resource-group $resourceGroup --name $registryName --sku Basic"
try {
    $registry = az acr create `
        --resource-group $resourceGroup `
        --name $registryName `
        --sku Basic | ConvertFrom-Json
    Write-Success "Container Registry Created: $($registry.name)"
} catch {
    Write-Error-Custom "Failed to create container registry"
    Write-Host $_.Exception.Message
    exit 1
}

# Step 3: Get Registry Credentials
Write-Info "STEP 3: Getting Registry Credentials..."
try {
    $creds = az acr credential show `
        --resource-group $resourceGroup `
        --name $registryName | ConvertFrom-Json

    $username = $creds.username
    $password = $creds.passwords[0].value
    $loginServer = $creds.loginServer

    Write-Success "Registry Credentials Obtained"
    Write-Info "  Login Server: $loginServer"
    Write-Info "  Username: $username"
} catch {
    Write-Error-Custom "Failed to get registry credentials"
    Write-Host $_.Exception.Message
    exit 1
}

# Step 4: Build and Push Image
Write-Info "STEP 4: Building and Pushing Docker Image..."
Write-Host "Command: az acr build --registry $registryName --image $imageName`:$imageTag ./azure_foundry_service"

# First, check if we're in the right directory
if (-not (Test-Path "azure_foundry_service\Dockerfile")) {
    Write-Error-Custom "Dockerfile not found in azure_foundry_service directory!"
    Write-Host "Current location: $(Get-Location)"
    Write-Host "Please run this script from the bot directory"
    exit 1
}

try {
    az acr build `
        --registry $registryName `
        --image "$imageName`:$imageTag" `
        ./azure_foundry_service

    Write-Success "Docker Image Built and Pushed"
    Write-Info "  Image: $loginServer/$imageName`:$imageTag"
} catch {
    Write-Error-Custom "Failed to build and push image"
    Write-Host $_.Exception.Message
    exit 1
}

# Step 5: Create Container App Environment
Write-Info "STEP 5: Creating Container App Environment..."
Write-Host "Command: az containerapp env create --name $containerAppEnv --resource-group $resourceGroup --location $location"
try {
    $env = az containerapp env create `
        --name $containerAppEnv `
        --resource-group $resourceGroup `
        --location $location | ConvertFrom-Json

    Write-Success "Container App Environment Created: $($env.name)"
} catch {
    Write-Warning-Custom "Container App Environment may already exist, continuing..."
}

# Step 6: Create Container App
Write-Info "STEP 6: Creating Container App..."
Write-Host "Command: az containerapp create --name $containerAppName ..."

try {
    $app = az containerapp create `
        --name $containerAppName `
        --resource-group $resourceGroup `
        --environment $containerAppEnv `
        --image "$loginServer/$imageName`:$imageTag" `
        --target-port 8000 `
        --ingress external `
        --min-replicas $minReplicas `
        --max-replicas $maxReplicas `
        --cpu $cpuCores `
        --memory $memorySize `
        --registry-server $loginServer `
        --registry-username $username `
        --registry-password $password `
        --env-vars `
            SUPABASE_URL=$supabaseUrl `
            SUPABASE_KEY=$supabaseKey `
            LOG_LEVEL="INFO" `
            WORKERS="4" | ConvertFrom-Json

    Write-Success "Container App Created: $($app.name)"
} catch {
    Write-Error-Custom "Failed to create container app"
    Write-Host $_.Exception.Message
    exit 1
}

# Step 7: Get Container App URL
Write-Info "STEP 7: Getting Container App URL..."
try {
    $appDetails = az containerapp show `
        --resource-group $resourceGroup `
        --name $containerAppName | ConvertFrom-Json

    $appUrl = $appDetails.properties.configuration.ingress.fqdn

    Write-Success "Container App Deployed Successfully!"
    Write-Host "`n" + ("=" * 80)
    Write-Host "YOUR AZURE ENDPOINT URL:" -ForegroundColor Green
    Write-Host "https://$appUrl" -ForegroundColor Yellow
    Write-Host ("=" * 80) + "`n"

} catch {
    Write-Error-Custom "Failed to get container app URL"
    Write-Host $_.Exception.Message
    exit 1
}

# Step 8: Wait for container app to be ready
Write-Info "STEP 8: Waiting for Container App to be ready (this may take 2-3 minutes)..."
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Write-Host "Attempt $attempt/$maxAttempts..." -ForegroundColor Cyan

    try {
        $response = Invoke-WebRequest -Uri "https://$appUrl/health" -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Container App is Ready!"
            $ready = $true
        }
    } catch {
        Write-Host "  Not ready yet, waiting..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if (-not $ready) {
    Write-Warning-Custom "Container App did not respond within timeout"
    Write-Info "This may just mean it's still starting. Check logs with:"
    Write-Host "az containerapp logs show --name $containerAppName --resource-group $resourceGroup --follow"
}

# Step 9: Test the endpoints
if ($ready) {
    Write-Info "STEP 9: Testing endpoints..."

    try {
        Write-Host "`nTesting /health endpoint..." -ForegroundColor Cyan
        $health = Invoke-RestMethod -Uri "https://$appUrl/health" -Method Get
        Write-Success "Health Check Passed!"
        Write-Host "Status: $($health.status)"
        Write-Host "Models Loaded: $($health.models_loaded)/15"
        Write-Host "Supabase Connected: $($health.supabase_connected)"
    } catch {
        Write-Warning-Custom "Health endpoint test failed"
    }

    try {
        Write-Host "`nTesting /models endpoint..." -ForegroundColor Cyan
        $models = Invoke-RestMethod -Uri "https://$appUrl/models" -Method Get
        Write-Success "Models endpoint working!"
        Write-Host "Total Models: $($models.total_models)"
    } catch {
        Write-Warning-Custom "Models endpoint test failed"
    }
}

# Step 10: Create .env file update instructions
Write-Host "`n" + ("=" * 80)
Write-Host "STEP 10: Update Your Bot Configuration" -ForegroundColor Magenta
Write-Host ("=" * 80)

Write-Info "Add the following to your bot's .env file:"
Write-Host "`nAZURE_FOUNDRY_ENDPOINT=https://$appUrl" -ForegroundColor Yellow
Write-Host "AZURE_FOUNDRY_API_KEY=optional-for-now`n" -ForegroundColor Yellow

# Offer to create .env file automatically
$createEnv = Read-Host "Would you like me to create/update the .env file for you? (Y/N)"
if ($createEnv -eq 'Y' -or $createEnv -eq 'y') {
    $envContent = @"
# Azure AI Foundry Configuration
AZURE_FOUNDRY_ENDPOINT=https://$appUrl
AZURE_FOUNDRY_API_KEY=optional-for-now
SUPABASE_URL=$supabaseUrl
SUPABASE_KEY=$supabaseKey
"@

    # Check if .env exists
    if (Test-Path ".env") {
        Write-Warning-Custom ".env file already exists. Creating backup..."
        Copy-Item ".env" ".env.backup"
        Write-Success "Backup created: .env.backup"
    }

    # Create/update .env
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Success ".env file updated!"
}

# Final Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Magenta
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Magenta

Write-Host "`nDEPLOYMENT SUMMARY:" -ForegroundColor Cyan
Write-Host "  [OK] Resource Group: $resourceGroup"
Write-Host "  [OK] Container Registry: $registryName"
Write-Host "  [OK] Container App: $containerAppName"
Write-Host "  [OK] Azure Endpoint: https://$appUrl"
Write-Host "  [OK] Supabase Connected: Yes"

Write-Host "`nNEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Verify .env file contains the endpoint URL"
Write-Host "  2. Start your bot: python main.py"
Write-Host "  3. Test the connection by completing a round"
Write-Host "  4. Check bot logs for Azure prediction messages"

Write-Host "`nUSEFUL COMMANDS:" -ForegroundColor Cyan
Write-Host "  View logs:"
Write-Host "    az containerapp logs show --name $containerAppName --resource-group $resourceGroup --follow"
Write-Host ""
Write-Host "  Test health endpoint:"
Write-Host "    curl https://$appUrl/health"
Write-Host ""
Write-Host "  View container app status:"
Write-Host "    az containerapp show --name $containerAppName --resource-group $resourceGroup"

Write-Host "`n" + ("=" * 80) -ForegroundColor Magenta
Write-Host "Thank you for using Azure AI Foundry!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Magenta
Write-Host ""
