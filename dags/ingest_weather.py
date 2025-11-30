# dags/ingest_weather.py

from airflow.decorators import dag, task
import pendulum
from airflow.models import Variable
from datetime import timedelta

# Open-Meteo API endpoint and parameters
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
LAT, LON = 24.86, 67.01  # Karachi

RAW_DIR = "/opt/airflow/data/raw"
PROC_DIR = "/opt/airflow/data/processed"

default_args = {"retries": 1, "retry_delay": timedelta(minutes=2)}

@dag(schedule="@hourly", start_date=pendulum.datetime(2025, 11, 29, 0, 0, 0, tz="UTC"), catchup=False, default_args=default_args, tags=["rps", "ingest"])
def ingest_weather():

    @task()
    def extract_raw():
        """Extract weather data from Open-Meteo API"""
        import os, requests, json, datetime
        os.makedirs(RAW_DIR, exist_ok=True)
        params = {
            "latitude": LAT,
            "longitude": LON,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,weathercode,pressure_msl,cloudcover,windspeed_10m,winddirection_10m",
            "current_weather": True,
            "timezone": "auto"
        }
        r = requests.get(OPENMETEO_URL, params=params, timeout=30)
        r.raise_for_status()
        payload = r.json()
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{RAW_DIR}/weather_{ts}.json"
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"✅ Extracted weather data to: {out_path}")
        return out_path

    @task()
    def dq_check(raw_path: str):
        """Data Quality Check: Validate extracted data"""
        import json
        with open(raw_path) as f:
            payload = json.load(f)
        hourly = payload.get("hourly", {})
        temps = hourly.get("temperature_2m", [])
        if not temps or len(temps) < 6:
            raise ValueError(f"❌ DQ FAIL: hourly temperature_2m data missing or too short (got {len(temps)} records, need ≥6)")
        nulls = sum(1 for t in temps if t is None)
        null_ratio = nulls / max(1, len(temps))
        if null_ratio > 0.01:
            raise ValueError(f"❌ DQ FAIL: null ratio {null_ratio:.3f} > 0.01 (1%)")
        print(f"✅ Data Quality Check Passed: {len(temps)} records, {null_ratio:.1%} nulls")
        return True

    @task()
    def transform_features(raw_path: str):
        """Transform raw data into features for prediction"""
        import json, pandas as pd, datetime, os
        os.makedirs(PROC_DIR, exist_ok=True)
        with open(raw_path) as f:
            payload = json.load(f)
        hourly = payload["hourly"]
        n = len(hourly["time"])
        rows = []
        for i in range(n):
            rows.append({
                "dt": pd.to_datetime(hourly["time"][i]),
                "temp": hourly["temperature_2m"][i],
                "humidity": hourly.get("relative_humidity_2m", [None]*n)[i],
                "pressure": hourly.get("pressure_msl", [None]*n)[i],
                "wind_speed": hourly.get("windspeed_10m", [None]*n)[i],
                "clouds": hourly.get("cloudcover", [None]*n)[i]
            })
        df = pd.DataFrame(rows).sort_values("dt").reset_index(drop=True)
        df["lag1"] = df["temp"].shift(1)
        df["lag3"] = df["temp"].shift(3)
        df["roll3"] = df["temp"].rolling(window=3, min_periods=1).mean()
        df["hour"] = df["dt"].dt.hour
        df["day_of_week"] = df["dt"].dt.dayofweek
        df["target_temp_4h"] = df["temp"].shift(-4)
        df = df.dropna(subset=["target_temp_4h"])
        out_file = f"{PROC_DIR}/weather_processed_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.parquet"
        df.to_parquet(out_file, index=False)
        print(f"✅ Transformed {len(df)} records with {len(df.columns)} features")
        print(f"   Saved to: {out_file}")
        return out_file

    @task()
    def profile_and_log(processed_path: str):
        """Generate data profile report and log to MLflow"""
        import pandas as pd
        from ydata_profiling import ProfileReport
        import mlflow, os, datetime
        df = pd.read_parquet(processed_path)
        prof = ProfileReport(df, title="Weather Data Profile", minimal=True, explorative=True)
        html_path = processed_path.replace(".parquet", "_profile.html")
        prof.to_file(html_path)
        artifact_dir = "/opt/airflow/data/mlflow_artifacts"
        os.makedirs(artifact_dir, exist_ok=True)
        os.environ["MLFLOW_ARTIFACT_URI"] = artifact_dir
        mlflow.set_tracking_uri("http://mlflow:5000")
        mlflow.set_experiment("weather_ingestion")
        with mlflow.start_run(run_name=f"profile_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}"):
            mlflow.log_param("dataset_size", len(df))
            mlflow.log_param("num_features", len(df.columns))
            mlflow.log_param("collection_time", datetime.datetime.utcnow().isoformat())
            mlflow.log_artifact(html_path, artifact_path="profiles")
            mlflow.log_artifact(processed_path, artifact_path="datasets")
        print(f"✅ Profile report logged to MLflow: {html_path}")
        return html_path

    @task()
    def dvc_add_and_push(processed_path: str):
        """Version the processed dataset with DVC"""
        import subprocess, pathlib
        try:
            result = subprocess.run(
                ["dvc", "add", processed_path],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ DVC add: {result.stdout}")
            dvc_file = f"{processed_path}.dvc"
            subprocess.run(["git", "add", dvc_file], check=False)
            subprocess.run(
                ["git", "commit", "-m", f"Add processed dataset {pathlib.Path(processed_path).name}"],
                check=False
            )
            # Push to DVC remote
            subprocess.check_call(["dvc", "push"])
            print(f"✅ Dataset versioned and pushed with DVC: {dvc_file}")
            return dvc_file
        except subprocess.CalledProcessError as e:
            print(f"⚠️  DVC error: {e.stderr}")
            print("   Continuing without DVC versioning...")
            return None


    raw = extract_raw()
    ok = dq_check(raw)
    proc = transform_features(raw)
    prof = profile_and_log(proc)
    push = dvc_add_and_push(proc)

    @task()
    def train_model(processed_path: str):
        """Train model and log experiment to MLflow"""
        import subprocess, sys, os
        # Use the latest processed file
        env = os.environ.copy()
        env["PROCESSED_DATA_PATH"] = processed_path
        env["MLFLOW_EXPERIMENT_NAME"] = "weather-forecast"
        # Optionally set MLflow tracking URI here if using Dagshub later
        env["MLFLOW_TRACKING_URI"] = "https://dagshub.com/AKProgramer/weather-mlops.mlflow"
        result = subprocess.run([sys.executable, "train.py"], env=env, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise RuntimeError("Model training failed")
        print("\u2705 Model training and MLflow logging complete.")
        return True

    train = train_model(proc)

ingest_weather = ingest_weather()
