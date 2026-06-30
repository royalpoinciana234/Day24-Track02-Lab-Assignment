# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    df = pd.read_csv("data/raw/patients_raw.csv")
    return JSONResponse(content=df.head(10).to_dict(orient="records"))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    df = pd.read_csv("data/raw/patients_raw.csv")
    df_anon = anonymizer.anonymize_dataframe(df)
    return JSONResponse(content=df_anon.head(10).to_dict(orient="records"))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    df = pd.read_csv("data/raw/patients_raw.csv")
    metrics = (
        df.groupby("benh")
          .agg(so_benh_nhan=("patient_id", "count"))
          .reset_index()
          .to_dict(orient="records")
    )
    return JSONResponse(content={"metrics": metrics})

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    df = pd.read_csv("data/raw/patients_raw.csv")
    if patient_id not in df["patient_id"].values:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    df = df[df["patient_id"] != patient_id]
    df.to_csv("data/raw/patients_raw.csv", index=False)
    return {"deleted": patient_id}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
