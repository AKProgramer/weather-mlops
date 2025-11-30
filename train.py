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

        if X_aligned.shape[0] < 4:
            msg = f"Not enough data after cleaning to train/test split (n={X_aligned.shape[0]})."
            print(msg)
            mlflow.set_tag("training_skipped", "true")
            mlflow.log_param("num_rows_after_clean", int(X_aligned.shape[0]))
            return

        # Train/test split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X_aligned, y_aligned, test_size=0.2, random_state=42
        )

        mlflow.log_param("train_size", int(X_train.shape[0]))
        mlflow.log_param("test_size", int(X_test.shape[0]))


        model = LinearRegression()

        try:
            model.fit(X_train, y_train)

            # Train metrics
            train_preds = model.predict(X_train)
            train_mse = mean_squared_error(y_train, train_preds)
            train_rmse = float(np.sqrt(train_mse))
            train_mae = mean_absolute_error(y_train, train_preds)
            train_r2 = r2_score(y_train, train_preds)

            # Test metrics
            test_preds = model.predict(X_test)
            test_mse = mean_squared_error(y_test, test_preds)
            test_rmse = float(np.sqrt(test_mse))
            test_mae = mean_absolute_error(y_test, test_preds)
            test_r2 = r2_score(y_test, test_preds)

            # Log metrics
            mlflow.log_param("model_type", "LinearRegression")
            mlflow.log_metric("train_rmse", train_rmse)
            mlflow.log_metric("train_mae", train_mae)
            mlflow.log_metric("train_r2", train_r2)
            mlflow.log_metric("test_rmse", test_rmse)
            mlflow.log_metric("test_mae", test_mae)
            mlflow.log_metric("test_r2", test_r2)
            mlflow.log_param("num_rows_after_clean", int(X_aligned.shape[0]))

            # ---- DAGSHUB SAFE MODEL LOGGING ----
            # Save model locally first
            local_model_path = "model"
            mlflow.sklearn.save_model(model, local_model_path)

            # Upload model folder as artifacts instead of using model registry
            mlflow.log_artifact(local_model_path)

            print(f"Logged run: TRAIN_RMSE={train_rmse:.3f}, TEST_RMSE={test_rmse:.3f}, TRAIN_R2={train_r2:.3f}, TEST_R2={test_r2:.3f}")

        except Exception as e:
            mlflow.set_tag("training_error", str(e))
            print("Model training failed:", e)
            raise


if __name__ == "__main__":
    train_and_log()
