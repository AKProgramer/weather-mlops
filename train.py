import os
import pandas as pd
import numpy as np
import mlflow

# Set MLflow tracking URI to Dagshub
mlflow.set_tracking_uri("https://dagshub.com/AKProgramer/weather-mlops.mlflow")

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Find the latest processed parquet file automatically
import glob
processed_files = glob.glob("data/processed/*.parquet")
if not processed_files:
    raise FileNotFoundError("No processed parquet files found in data/processed/")

PROCESSED_DATA_PATH = max(processed_files, key=os.path.getctime)
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "weather-forecast")


def load_data(path):
    return pd.read_parquet(path)


def train_and_log():
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run():
        df = load_data(PROCESSED_DATA_PATH)

        # Simple feature/target split (customize as needed)
        if "target" in df.columns:
            y = df["target"]
        else:
            y = df.iloc[:, -1]

        X = df.drop(columns=["target"], errors="ignore")

        # Drop datetime columns
        datetime_cols = X.select_dtypes(include=["datetime", "datetimetz", "datetime64[ns]"]).columns.tolist()
        if "dt" in X.columns:
            datetime_cols.append("dt")

        X = X.drop(columns=list(set(datetime_cols)), errors="ignore")

        # Ensure X and y aligned
        Xy = pd.concat([X, y.rename("__target__")], axis=1)
        Xy = Xy.dropna()

        y_aligned = Xy["__target__"]
        X_aligned = Xy.drop(columns=["__target__"])

        if X_aligned.shape[0] < 2:
            msg = f"Not enough data after cleaning to train model (n={X_aligned.shape[0]})."
            print(msg)
            mlflow.set_tag("training_skipped", "true")
            mlflow.log_param("num_rows_after_clean", int(X_aligned.shape[0]))
            return

        model = LinearRegression()

        try:
            model.fit(X_aligned, y_aligned)
            preds = model.predict(X_aligned)

            mse = mean_squared_error(y_aligned, preds)
            rmse = float(np.sqrt(mse))
            mae = mean_absolute_error(y_aligned, preds)
            r2 = r2_score(y_aligned, preds)

            # Log metrics
            mlflow.log_param("model_type", "LinearRegression")
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("r2", r2)
            mlflow.log_param("num_rows_after_clean", int(X_aligned.shape[0]))

            # ---- DAGSHUB SAFE MODEL LOGGING ----
            # Save model locally first
            local_model_path = "model"
            mlflow.sklearn.save_model(model, local_model_path)

            # Upload model folder as artifacts instead of using model registry
            mlflow.log_artifact(local_model_path)

            print(f"Logged run: RMSE={rmse:.3f}, MAE={mae:.3f}, R2={r2:.3f}")

        except Exception as e:
            mlflow.set_tag("training_error", str(e))
            print("Model training failed:", e)
            raise


if __name__ == "__main__":
    train_and_log()
