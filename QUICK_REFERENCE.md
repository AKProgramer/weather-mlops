# 🚀 Quick Reference Card

## Essential Commands

### Docker Management
```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View running services
docker compose ps

# View logs (specific service)
docker compose logs -f airflow-scheduler
docker compose logs -f mlflow

# Restart a service
docker compose restart airflow-scheduler

# Rebuild containers (after code changes)
docker compose down
docker compose up -d --build
```

### DVC Commands
```powershell
# Initialize DVC
dvc init

# Add remote
dvc remote add -d minio s3://dvc-storage
dvc remote modify minio endpointurl http://localhost:9000
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin

# Check status
dvc status

# Add file to tracking
dvc add data/processed/dataset.parquet

# Push to remote
dvc push

# Pull from remote
dvc pull

# List remotes
dvc remote list
```

### Airflow Commands
```powershell
# List all DAGs
docker compose exec airflow-apiserver airflow dags list

# Test a specific task
docker compose exec airflow-apiserver airflow tasks test ingest_weather extract_raw 2024-01-01

# Trigger DAG manually
docker compose exec airflow-apiserver airflow dags trigger ingest_weather

# Pause/Unpause DAG
docker compose exec airflow-apiserver airflow dags pause ingest_weather
docker compose exec airflow-apiserver airflow dags unpause ingest_weather
```

### Data Inspection
```powershell
# View raw JSON data
cat data/raw/weather_*.json | jq .

# Check Parquet file with Python
python -c "import pandas as pd; df = pd.read_parquet('data/processed/weather_*.parquet'); print(df.info()); print(df.head())"

# Count files
(dir data/raw/*.json).Count
(dir data/processed/*.parquet).Count
```

---

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow UI | http://localhost:8080 | airflow / airflow |
| MLflow UI | http://localhost:5000 | (none) |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| MinIO API | http://localhost:9000 | (for DVC) |

---

## 📁 Key File Locations

```
RPS/
├── dags/ingest_weather.py          # Main DAG definition
├── data/raw/                       # Raw API responses
├── data/processed/                 # Processed datasets
├── .env                            # Environment variables
├── .dvc/config                     # DVC configuration
└── logs/                           # Airflow execution logs
```

---

## ⚙️ Environment Variables (.env)

```env
AIRFLOW_UID=50000
OPENWEATHER_API_KEY=your_key_here
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MLFLOW_TRACKING_URI=http://mlflow:5000
```

---

## 🔍 Debugging Quick Tips

### Check Service Health
```powershell
# Test Airflow
curl http://localhost:8080/health

# Test MLflow
curl http://localhost:5000

# Test MinIO
curl http://localhost:9000
```

### View Logs
```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f airflow-scheduler

# Last 100 lines
docker compose logs --tail=100 airflow-worker
```

### Reset Everything
```powershell
# Stop and remove all containers, volumes, and data
docker compose down -v

# Remove data directories
rm -r data/raw/* -Force
rm -r data/processed/* -Force

# Start fresh
docker compose up -d
```

---

## 📊 DAG Schedule Patterns

```python
schedule_interval="@hourly"      # Every hour
schedule_interval="@daily"       # Once per day at midnight
schedule_interval="0 */6 * * *"  # Every 6 hours
schedule_interval="*/30 * * * *" # Every 30 minutes
schedule_interval=None           # Manual only
```

---

## 🎯 Common Tasks

### Add New Feature to Pipeline
1. Edit `dags/ingest_weather.py` → `transform_features()`
2. Add feature engineering logic
3. Save file (Airflow auto-reloads)
4. Trigger DAG to test

### Change Data Source Location
1. Edit `LAT, LON` variables in `dags/ingest_weather.py`
2. Or add Airflow Variables for dynamic configuration

### Export MLflow Artifacts
```powershell
# Open MLflow UI → Experiments → Select Run → Artifacts → Download
```

### Check Disk Usage
```powershell
# Docker volumes
docker system df

# Data directories
du -sh data/raw
du -sh data/processed
```

---

## 🆘 Emergency Commands

### Service Not Starting
```powershell
# Check what's using port 8080
netstat -ano | findstr :8080

# Kill process (replace PID)
taskkill /PID 12345 /F

# Or change port in docker-compose.yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

### Disk Full
```powershell
# Clean Docker system
docker system prune -a

# Remove old log files
rm logs/* -Force

# Remove old data
rm data/raw/weather_2024* -Force
```

### Reset Airflow Database
```powershell
docker compose down -v
docker compose up -d
# Wait for initialization
```

---

## 📧 Support Checklist

When asking for help, provide:
- [ ] Output of `docker compose ps`
- [ ] Relevant service logs (`docker compose logs <service>`)
- [ ] Airflow task log (from UI)
- [ ] DAG code snippet if modified
- [ ] Error message (full traceback)

---

**Save this file for quick reference during development!** 📌
