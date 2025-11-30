# Real-Time Predictive System (RPS) - Weather Forecasting

## 📊 Project Overview

A robust MLOps pipeline for real-time weather prediction using Apache Airflow, MLflow, and DVC. This system automatically:
- Fetches live weather data from OpenWeatherMap API
- Validates data quality with strict checks
- Engineers time-series features for temperature prediction
- Generates and logs data profiling reports
- Versions datasets using DVC with MinIO storage

**Predictive Task**: Predict temperature 4-6 hours ahead for Karachi using historical weather patterns.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ OpenWeatherMap  │────▶│   Airflow    │────▶│   MinIO     │
│      API        │     │   Pipeline   │     │ (DVC Remote)│
└─────────────────┘     └──────────────┘     └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │    MLflow    │
                        │   Tracking   │
                        └──────────────┘
```

### Components

1. **Apache Airflow**: Orchestrates ETL pipeline with CeleryExecutor
2. **PostgreSQL**: Airflow metadata database
3. **Redis**: Celery message broker
4. **MLflow**: Experiment tracking & artifact logging
5. **MinIO**: S3-compatible object storage for DVC
6. **DVC**: Data version control

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git
- Python 3.9+ (for local DVC setup)
- OpenWeatherMap API Key ([Get it here](https://openweathermap.org/api))

### Step 1: Clone and Setup

```powershell
# Clone the repository
git clone <your-repo-url>
cd RPS

# Initialize DVC
dvc init
```

### Step 2: Configure Environment

Edit `.env` file and add your OpenWeatherMap API key:

```env
OPENWEATHER_API_KEY=YOUR_API_KEY_HERE
```

### Step 3: Start Services

```powershell
# Start all services (Airflow, MLflow, MinIO, PostgreSQL, Redis)
docker compose up -d

# Wait ~2 minutes for initialization
docker compose ps
```

**Access Points:**
- 🌐 **Airflow UI**: http://localhost:8080 (airflow/airflow)
- 📊 **MLflow UI**: http://localhost:5000
- 🗄️ **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### Step 4: Configure Airflow Variables

1. Open Airflow UI: http://localhost:8080
2. Login with `airflow` / `airflow`
3. Go to **Admin → Variables**
4. Add variable:
   - **Key**: `OPENWEATHER_API_KEY`
   - **Value**: Your API key from OpenWeatherMap

### Step 5: Setup MinIO Bucket for DVC

1. Open MinIO Console: http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Create bucket named: **`dvc-storage`**
4. Set bucket access to **Public** (Buckets → dvc-storage → Access Policy → Public)

### Step 6: Configure DVC Remote

```powershell
# Run the setup script
.\setup_dvc.ps1

# Or manually:
dvc remote add -d minio s3://dvc-storage
dvc remote modify minio endpointurl http://localhost:9000
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin
```

### Step 7: Enable and Run the DAG

1. In Airflow UI, find `ingest_weather` DAG
2. Toggle it **ON** (switch on left side)
3. Click **Play** button to trigger manually
4. Watch the Graph view as tasks execute

---

## 📋 Pipeline Stages

### Stage 1: Extract Raw Data (`extract_raw`)
- Fetches current + 48h forecast from OpenWeatherMap API
- Saves raw JSON with timestamp: `data/raw/weather_YYYYMMDD_HHMMSS.json`
- **Output**: Path to raw JSON file

### Stage 2: Data Quality Check (`dq_check`)
- **✅ Passes if**:
  - ≥6 hourly records present
  - <1% null values in temperature data
- **❌ Fails pipeline if** checks don't pass

### Stage 3: Transform Features (`transform_features`)
- Creates time-series features:
  - Lag features (lag1, lag3)
  - Rolling mean (3-hour window)
  - Time encodings (hour, day_of_week)
  - Target variable: temperature 4 hours ahead
- Saves as Parquet: `data/processed/weather_processed_*.parquet`
- **Output**: Path to processed Parquet file

### Stage 4: Profile & Log (`profile_and_log`)
- Generates Pandas Profiling HTML report
- Logs to MLflow:
  - Dataset metadata (size, features, timestamp)
  - Profile report as artifact
  - Processed dataset as artifact
- **Output**: Path to profile HTML

### Stage 5: DVC Versioning (`dvc_add_and_push`)
- Adds processed dataset to DVC tracking
- Creates `.dvc` metadata file
- Pushes large file to MinIO storage
- Commits `.dvc` file to Git
- **Output**: Path to `.dvc` file

---

## 📁 Project Structure

```
RPS/
├── dags/
│   └── ingest_weather.py       # Main Airflow DAG
├── data/
│   ├── raw/                    # Raw API responses (JSON)
│   └── processed/              # Processed datasets (Parquet)
│       └── *.dvc               # DVC metadata files
├── logs/                       # Airflow execution logs
├── config/                     # Airflow config files
├── .env                        # Environment variables
├── .dvc/                       # DVC configuration
├── docker-compose.yaml         # Multi-service orchestration
├── requirements.txt            # Python dependencies
├── setup_dvc.ps1              # DVC setup script (Windows)
└── README.md                  # This file
```

---

## 🔧 Configuration Details

### Airflow DAG Configuration

```python
schedule_interval="@hourly"      # Runs every hour
start_date=days_ago(1)          # Started yesterday
catchup=False                    # Don't backfill historical runs
retries=1                        # Retry failed tasks once
retry_delay=2 minutes            # Wait 2 min before retry
```

### Data Quality Thresholds

- **Minimum Records**: 6 hourly forecasts
- **Max Null Ratio**: 1% (0.01)
- **Schema**: Must include `temp`, `humidity`, `pressure`, `dt`

### Feature Engineering

| Feature | Description | Type |
|---------|-------------|------|
| `temp`, `humidity`, `pressure` | Current measurements | Raw |
| `wind_speed`, `clouds` | Weather conditions | Raw |
| `lag1`, `lag3` | Temperature 1h/3h ago | Lag |
| `roll3` | 3-hour rolling mean | Rolling |
| `hour`, `day_of_week` | Time encodings | Temporal |
| `target_temp_4h` | Temperature 4h ahead | Target |

---

## 🐛 Troubleshooting

### DAG Not Appearing?

```powershell
# Check Airflow scheduler logs
docker compose logs airflow-scheduler -f

# Verify DAG file syntax
docker compose exec airflow-apiserver airflow dags list
```

### API Key Errors?

1. Verify key in Airflow UI: **Admin → Variables → OPENWEATHER_API_KEY**
2. Test API manually:
   ```powershell
   curl "https://api.openweathermap.org/data/2.5/onecall?lat=24.86&lon=67.01&appid=YOUR_KEY"
   ```

### DVC Push Fails?

```powershell
# Check MinIO connection
dvc remote list
dvc doctor

# Verify bucket exists in MinIO Console
# http://localhost:9001 → Buckets → dvc-storage
```

### MLflow Not Logging?

```powershell
# Check MLflow service
docker compose ps mlflow
docker compose logs mlflow

# Test connection from Airflow worker
docker compose exec airflow-worker curl http://mlflow:5000/health
```

---

## 📊 Monitoring & Validation

### Check Pipeline Execution

1. **Airflow UI**: http://localhost:8080
   - Graph view shows task dependencies
   - Task logs show detailed output
   - Gantt chart shows execution timeline

2. **MLflow UI**: http://localhost:5000
   - View experiment runs
   - Download profiling reports
   - Track dataset metadata

3. **MinIO Console**: http://localhost:9001
   - Verify datasets uploaded to `dvc-storage` bucket
   - Check file sizes and timestamps

### Verify Data Quality

```powershell
# Check raw data
cat data/raw/weather_*.json | jq '.hourly | length'

# Check processed data
pip install pandas pyarrow
python -c "import pandas as pd; df = pd.read_parquet('data/processed/weather_processed_latest.parquet'); print(df.info())"

# Check DVC tracking
dvc status
dvc diff
```

---

## 🎯 Next Steps (Phase II & Beyond)

### Phase II: Model Training & Deployment
- [ ] Add model training task to DAG
- [ ] Implement hyperparameter tuning with Optuna
- [ ] Register models in MLflow Model Registry
- [ ] Deploy model as REST API (FastAPI/Flask)

### Phase III: Monitoring & Drift Detection
- [ ] Implement concept drift detection (Evidently AI)
- [ ] Add model performance monitoring
- [ ] Set up alerting for degraded predictions
- [ ] Automate model retraining on drift detection

### Phase IV: Production Hardening
- [ ] Move to cloud infrastructure (AWS/Azure/GCP)
- [ ] Implement authentication & authorization
- [ ] Add comprehensive logging (ELK stack)
- [ ] Set up CI/CD pipelines (GitHub Actions)
- [ ] Configure backup & disaster recovery

---

## 📝 Key Deliverables (Phase I Checklist)

- [x] Problem Selection: Temperature forecasting (4-6h ahead)
- [x] API Integration: OpenWeatherMap with hourly forecasts
- [x] Airflow DAG: Scheduled ETL pipeline (@hourly)
- [x] Data Quality Gate: ≥6 records, <1% nulls
- [x] Feature Engineering: Lags, rolling means, time features
- [x] Pandas Profiling: Automated report generation
- [x] MLflow Integration: Artifact logging to tracking server
- [x] DVC Versioning: Dataset versioning with MinIO remote
- [x] Documentation: Complete setup & usage guide

---

## 🤝 Team Members

- [Add your names here]

## 📄 License

This project is for educational purposes as part of an MLOps course.

---

## 🔗 Resources

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [DVC User Guide](https://dvc.org/doc/user-guide)
- [OpenWeatherMap API](https://openweathermap.org/api/one-call-3)
- [Pandas Profiling](https://ydata-profiling.ydata.ai/)

---

**Questions?** Check the troubleshooting section or review Airflow task logs for detailed error messages.
