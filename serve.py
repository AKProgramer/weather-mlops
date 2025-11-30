import os
import pickle
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import numpy as np
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

MODEL_PATH = os.getenv("MODEL_PATH", "model/model.pkl")

app = FastAPI()

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total number of API requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
DRIFT_COUNT = Counter('data_drift_requests_total', 'Total number of requests with data drift')

class PredictRequest(BaseModel):
    features: list


@app.on_event("startup")
def load_model():
    global model
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        print(f"Failed to load model: {e}")
        model = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration)
    
    return response


@app.post("/predict")
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Check for data drift (basic proxy: features outside -1000 to 1000)
    drift = any(abs(f) > 1000 for f in req.features)
    if drift:
        DRIFT_COUNT.inc()
    
    X = np.array(req.features).reshape(1, -1)
    try:
        pred = model.predict(X)
        return {"prediction": pred.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/metrics")
def metrics():
    return generate_latest(), {"Content-Type": CONTENT_TYPE_LATEST}
