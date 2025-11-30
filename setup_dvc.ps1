# Setup DVC with MinIO remote storage (Windows PowerShell)

# Initialize DVC (if not already done)
dvc init --no-scm
if ($LASTEXITCODE -ne 0) { 
    Write-Host "DVC already initialized or error occurred" -ForegroundColor Yellow
}

# Configure MinIO as remote storage
dvc remote add -d minio s3://dvc-storage
dvc remote modify minio endpointurl http://localhost:9000
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin

Write-Host "`nDVC remote configured!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Go to http://localhost:9001" -ForegroundColor White
Write-Host "2. Login with minioadmin/minioadmin" -ForegroundColor White
Write-Host "3. Create bucket named 'dvc-storage'" -ForegroundColor White
