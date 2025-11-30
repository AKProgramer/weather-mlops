import os
import pickle
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd

MODEL_PATH = os.getenv("MODEL_PATH", "model/model.pkl")

app = FastAPI()

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

@app.post("/predict")
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    X = np.array(req.features).reshape(1, -1)
    try:
        pred = model.predict(X)
        return {"prediction": pred.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
