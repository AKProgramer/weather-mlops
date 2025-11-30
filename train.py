import os
import pandas as pd
import numpy as np
import mlflow
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Paths
PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "data/processed/weather.parquet")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "weather-forecast")


def load_data(path):
    return pd.read_parquet(path)


def train_and_log():
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run():
        df = load_data(PROCESSED_DATA_PATH)
        # Simple feature/target split (customize as needed)
        X = df.drop(columns=["target"], errors="ignore")
        y = df["target"] if "target" in df.columns else df.iloc[:, -1]
        model = LinearRegression()
        model.fit(X, y)
        preds = model.predict(X)
        rmse = mean_squared_error(y, preds, squared=False)
        mae = mean_absolute_error(y, preds)
        r2 = r2_score(y, preds)
        mlflow.log_param("model_type", "LinearRegression")
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2", r2)
        mlflow.sklearn.log_model(model, "model")
        print(f"Logged run: RMSE={rmse:.3f}, MAE={mae:.3f}, R2={r2:.3f}")

if __name__ == "__main__":
    train_and_log()
