# Dockerfile for FastAPI model serving
FROM python:3.12-slim
WORKDIR /app
COPY serve.py ./
COPY model ./model
RUN pip install fastapi uvicorn scikit-learn numpy pandas
EXPOSE 8000
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]