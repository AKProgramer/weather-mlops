# Custom Airflow Dockerfile for your MLOps stack
FROM apache/airflow:3.1.3

USER airflow

# Install required Python packages
RUN pip install --no-cache-dir pandas requests ydata-profiling mlflow dvc[s3] pyarrow fastparquet
