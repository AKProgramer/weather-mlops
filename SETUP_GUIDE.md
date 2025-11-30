# 🎓 Phase I Complete Setup Guide - Step by Step

## ✅ What You've Built So Far

Your pipeline now includes:
- ✅ Apache Airflow with CeleryExecutor
- ✅ MLflow tracking server for experiment logging
- ✅ MinIO for S3-compatible object storage
- ✅ DVC for data versioning
- ✅ Complete ETL DAG with quality gates
- ✅ Automated data profiling and artifact logging

---

## 🚀 Complete Setup Process (30 minutes)

### Phase 1: Start Infrastructure (5 minutes)

```powershell
# 1. Navigate to project directory
cd D:\RPS

# 2. Start all services
docker compose up -d

# 3. Wait for initialization (check logs)
docker compose logs -f airflow-init

# Press Ctrl+C when you see "Airflow is ready"

# 4. Verify all services are running
docker compose ps

# Expected output: All services should show "Up" status
```

### Phase 2: Configure Airflow (5 minutes)

```powershell
# 1. Open Airflow UI
# Navigate to: http://localhost:8080
# Login: airflow / airflow

# 2. Add API Key Variable
#    - Click Admin → Variables
#    - Click "+" (Add a new record)
#    - Key: OPENWEATHER_API_KEY
#    - Val: YOUR_API_KEY_FROM_OPENWEATHERMAP
#    - Click Save

# 3. Verify DAG is visible
#    - Click "DAGs" in top menu
#    - Look for "ingest_weather" DAG
#    - Should show as "Paused" (toggle is OFF/gray)
```

**Get API Key**: 
1. Go to https://openweathermap.org/api
2. Sign up for free account
3. Get API key from: https://home.openweathermap.org/api_keys

### Phase 3: Setup MinIO Storage (3 minutes)

```powershell
# 1. Open MinIO Console
# Navigate to: http://localhost:9001
# Login: minioadmin / minioadmin

# 2. Create DVC Bucket
#    - Click "Buckets" in left menu
#    - Click "Create Bucket" button
#    - Bucket Name: dvc-storage
#    - Click "Create Bucket"

# 3. Set Access Policy
#    - Click on "dvc-storage" bucket
#    - Go to "Access" tab
#    - Change access to "Public" (for local testing)
#    - Click Save
```

### Phase 4: Initialize DVC (5 minutes)

```powershell
# 1. Initialize DVC (if not done)
dvc init

# 2. Configure DVC remote
.\setup_dvc.ps1

# OR manually:
dvc remote add -d minio s3://dvc-storage
dvc remote modify minio endpointurl http://localhost:9000
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin

# 3. Verify configuration
dvc remote list
# Should show: minio   s3://dvc-storage

# 4. Test connection
dvc status
```

### Phase 5: Test the Pipeline (10 minutes)

```powershell
# 1. Run health check
.\test_setup.ps1

# 2. Enable the DAG in Airflow UI
#    - Go to http://localhost:8080
#    - Find "ingest_weather" DAG
#    - Toggle switch to ON (blue/green)

# 3. Trigger manual run
#    - Click the "Play" button (▶) on the right
#    - Select "Trigger DAG"
#    - Click "Trigger"

# 4. Monitor execution
#    - Click on the DAG name "ingest_weather"
#    - Click "Graph" view
#    - Watch tasks turn green as they complete
#    - Click on tasks to see logs

# 5. Check outputs
#    - Raw data: D:\RPS\data\raw\weather_*.json
#    - Processed: D:\RPS\data\processed\weather_*.parquet
#    - Profiles: D:\RPS\data\processed\weather_*_profile.html
```

---

## 📊 Verification Checklist

After pipeline runs successfully, verify:

### ✅ Data Files Created

```powershell
# Check raw data
dir data\raw\weather_*.json

# Check processed data
dir data\processed\weather_*.parquet

# Check profile reports
dir data\processed\*_profile.html
```

### ✅ MLflow Logged Artifacts

1. Open http://localhost:5000
2. Click "weather_ingestion" experiment
3. Click latest run
4. Check "Artifacts" tab shows:
   - `profiles/` folder with HTML report
   - `datasets/` folder with Parquet file

### ✅ DVC Versioned Data

```powershell
# Check .dvc files created
dir data\processed\*.dvc

# Check DVC status
dvc status

# Verify files in MinIO
# Go to http://localhost:9001 → Buckets → dvc-storage
# Should see uploaded parquet files
```

### ✅ Airflow Execution Logs

1. In Airflow UI, click on DAG run
2. Click each task (green boxes)
3. Click "Log" button
4. Verify you see:
   - ✅ Extracted weather data
   - ✅ Data Quality Check Passed
   - ✅ Transformed X records
   - ✅ Profile report logged to MLflow
   - ✅ Dataset versioned with DVC

---

## 🐛 Common Issues & Solutions

### Issue 1: DAG Not Showing in Airflow

**Symptoms**: Can't find `ingest_weather` in DAGs list

**Solution**:
```powershell
# Check scheduler logs
docker compose logs airflow-scheduler | Select-String -Pattern "ingest_weather"

# Check for Python errors
docker compose logs airflow-scheduler | Select-String -Pattern "ERROR"

# Restart scheduler
docker compose restart airflow-scheduler
```

### Issue 2: API Key Error

**Symptoms**: Task `extract_raw` fails with "API key missing"

**Solution**:
1. Verify variable in Airflow UI: Admin → Variables → OPENWEATHER_API_KEY
2. Make sure variable name is EXACTLY: `OPENWEATHER_API_KEY` (case-sensitive)
3. Test API key manually:
   ```powershell
   curl "https://api.openweathermap.org/data/2.5/onecall?lat=24.86&lon=67.01&appid=YOUR_KEY&units=metric"
   ```

### Issue 3: DVC Push Fails

**Symptoms**: Task `dvc_add_and_push` fails with connection error

**Solution**:
```powershell
# Check MinIO is running
docker compose ps minio

# Test MinIO connection
curl http://localhost:9000

# Verify bucket exists
# Go to http://localhost:9001 and check for 'dvc-storage'

# Re-configure DVC remote
dvc remote modify minio endpointurl http://localhost:9000
```

### Issue 4: MLflow Connection Error

**Symptoms**: Task `profile_and_log` fails with "Connection refused"

**Solution**:
```powershell
# Check MLflow service
docker compose ps mlflow
docker compose logs mlflow

# Test from Airflow worker
docker compose exec airflow-worker curl http://mlflow:5000/health

# Restart MLflow
docker compose restart mlflow
```

### Issue 5: Permission Errors

**Symptoms**: Can't write to data directories

**Solution**:
```powershell
# Create directories with correct permissions
New-Item -ItemType Directory -Path "data\raw" -Force
New-Item -ItemType Directory -Path "data\processed" -Force

# Check Airflow UID in .env
cat .env | Select-String "AIRFLOW_UID"

# Restart services
docker compose down
docker compose up -d
```

---

## 📈 Understanding the Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     ingest_weather DAG                       │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴─────────────┐
                │                          │
                ▼                          ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │   extract_raw()      │   │ Runs every hour      │
    │                      │   │ (@hourly schedule)   │
    │ • Calls OWM API      │   └──────────────────────┘
    │ • Saves JSON to raw/ │
    └──────────────────────┘
                │
                ▼
    ┌──────────────────────┐
    │   dq_check()         │
    │                      │
    │ • Validates ≥6 recs  │
    │ • Checks <1% nulls   │
    │ • FAILS if not pass  │◄─── QUALITY GATE
    └──────────────────────┘
                │
                ▼
    ┌──────────────────────┐
    │ transform_features() │
    │                      │
    │ • Creates lags       │
    │ • Rolling means      │
    │ • Time encodings     │
    │ • Target variable    │
    │ • Saves Parquet      │
    └──────────────────────┘
                │
                ├─────────────────┬──────────────────┐
                ▼                 ▼                  ▼
    ┌──────────────────┐ ┌─────────────┐ ┌──────────────────┐
    │profile_and_log() │ │             │ │dvc_add_and_push()│
    │                  │ │ Both run    │ │                  │
    │• Pandas Profile  │ │ in parallel │ │• DVC add         │
    │• Log to MLflow   │ │             │ │• Push to MinIO   │
    └──────────────────┘ └─────────────┘ └──────────────────┘
```

---

## 🎯 Expected Outputs

### 1. Raw Data Sample (`data/raw/weather_20241130_123456.json`)

```json
{
  "lat": 24.86,
  "lon": 67.01,
  "timezone": "Asia/Karachi",
  "hourly": [
    {
      "dt": 1701345600,
      "temp": 28.5,
      "humidity": 65,
      "pressure": 1013,
      "wind_speed": 3.5,
      "clouds": 20
    },
    ...
  ]
}
```

### 2. Processed Data (`data/processed/weather_processed_*.parquet`)

| dt | temp | humidity | pressure | lag1 | lag3 | roll3 | hour | target_temp_4h |
|----|------|----------|----------|------|------|-------|------|----------------|
| 2024-11-30 12:00 | 28.5 | 65 | 1013 | 28.2 | 27.8 | 28.2 | 12 | 29.1 |

### 3. Profile Report (`data/processed/*_profile.html`)

Open in browser to see:
- Dataset statistics
- Variable distributions
- Correlations
- Missing values analysis
- Data quality alerts

### 4. MLflow Experiment Run

In http://localhost:5000:
- **Parameters**: dataset_size, num_features, collection_time
- **Artifacts**: 
  - profiles/weather_*_profile.html
  - datasets/weather_processed_*.parquet

### 5. DVC Files (`data/processed/*.dvc`)

```yaml
outs:
- md5: abc123def456...
  size: 12345
  path: weather_processed_20241130_123456.parquet
```

---

## 📝 Phase I Completion Checklist

Mark these off as you complete:

- [ ] All Docker services running (postgres, redis, airflow, mlflow, minio)
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] OpenWeatherMap API key added to Airflow Variables
- [ ] MinIO bucket `dvc-storage` created
- [ ] DVC initialized and remote configured
- [ ] `ingest_weather` DAG visible and enabled in Airflow
- [ ] DAG executed successfully (all tasks green)
- [ ] Raw JSON files in `data/raw/`
- [ ] Processed Parquet files in `data/processed/`
- [ ] Profile HTML reports generated
- [ ] MLflow experiment logged with artifacts
- [ ] DVC `.dvc` files created
- [ ] Data pushed to MinIO storage
- [ ] Health check script runs without errors
- [ ] Documentation reviewed and understood

---

## 🎓 What You've Learned

By completing Phase I, you've implemented:

1. **MLOps Infrastructure**:
   - Container orchestration with Docker Compose
   - Multi-service architecture (Airflow, MLflow, MinIO)
   - Persistent storage and networking

2. **Data Pipeline Orchestration**:
   - DAG design and task dependencies
   - Error handling and retries
   - Scheduled and manual execution

3. **Data Quality Engineering**:
   - Quality gates and validation checks
   - Automated failure mechanisms
   - Threshold-based monitoring

4. **Feature Engineering**:
   - Time-series feature creation
   - Lag features and rolling statistics
   - Target variable engineering

5. **Experiment Tracking**:
   - MLflow tracking server setup
   - Artifact logging and versioning
   - Metadata and parameter tracking

6. **Data Versioning**:
   - DVC for large file management
   - Remote storage configuration
   - Git integration for .dvc files

---

## ➡️ Next: Phase II Preview

Phase II will add:
- **Model Training**: Scikit-learn/XGBoost regression models
- **Hyperparameter Tuning**: Optuna optimization
- **Model Registry**: MLflow model versioning
- **Model Serving**: REST API deployment
- **Batch Predictions**: Automated inference

Get ready to transform your data pipeline into a complete ML system! 🚀

---

**Questions?** Review the troubleshooting section or check Airflow task logs for detailed diagnostics.
