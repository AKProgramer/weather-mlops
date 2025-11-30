#!/bin/bash
# Setup DVC with MinIO remote storage

# Initialize DVC (if not already done)
dvc init --no-scm || true

# Configure MinIO as remote storage
dvc remote add -d minio s3://dvc-storage
dvc remote modify minio endpointurl http://localhost:9000
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin

echo "DVC remote configured! Now create the bucket in MinIO:"
echo "1. Go to http://localhost:9001"
echo "2. Login with minioadmin/minioadmin"
echo "3. Create bucket named 'dvc-storage'"
