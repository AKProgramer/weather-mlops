# Test script to verify the pipeline setup
# Run this AFTER docker compose up -d and configuration is complete

Write-Host "`n🔍 RPS Pipeline Health Check" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Check if Docker containers are running
Write-Host "`n1️⃣ Checking Docker Services..." -ForegroundColor Yellow
$services = @("postgres", "redis", "airflow-scheduler", "airflow-apiserver", "mlflow", "minio")
foreach ($service in $services) {
    $status = docker compose ps $service --format "{{.Status}}"
    if ($status -like "*Up*") {
        Write-Host "   ✅ $service : Running" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $service : Not running" -ForegroundColor Red
    }
}

# Check if Airflow is accessible
Write-Host "`n2️⃣ Checking Airflow UI..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Airflow UI accessible at http://localhost:8080" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Airflow UI not accessible (may still be initializing...)" -ForegroundColor Red
}

# Check MLflow
Write-Host "`n3️⃣ Checking MLflow..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ MLflow UI accessible at http://localhost:5000" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ MLflow not accessible" -ForegroundColor Red
}

# Check MinIO
Write-Host "`n4️⃣ Checking MinIO..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9001" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ MinIO Console accessible at http://localhost:9001" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ MinIO not accessible" -ForegroundColor Red
}

# Check data directories
Write-Host "`n5️⃣ Checking Data Directories..." -ForegroundColor Yellow
$dirs = @("data\raw", "data\processed", "logs")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "   ✅ $dir exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dir missing" -ForegroundColor Red
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "      Created $dir" -ForegroundColor Yellow
    }
}

# Check DVC initialization
Write-Host "`n6️⃣ Checking DVC Setup..." -ForegroundColor Yellow
if (Test-Path ".dvc") {
    Write-Host "   ✅ DVC initialized" -ForegroundColor Green
    
    # Check remote
    $remotes = dvc remote list 2>$null
    if ($remotes) {
        Write-Host "   ✅ DVC remote configured: $remotes" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  DVC remote not configured. Run .\setup_dvc.ps1" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ DVC not initialized. Run: dvc init" -ForegroundColor Red
}

Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open Airflow UI: http://localhost:8080 (airflow/airflow)" -ForegroundColor White
Write-Host "   2. Add Variable: OPENWEATHER_API_KEY in Admin → Variables" -ForegroundColor White
Write-Host "   3. Create MinIO bucket 'dvc-storage' at http://localhost:9001" -ForegroundColor White
Write-Host "   4. Run: .\setup_dvc.ps1 to configure DVC remote" -ForegroundColor White
Write-Host "   5. Enable & trigger 'ingest_weather' DAG" -ForegroundColor White
Write-Host "`n" -ForegroundColor White
