from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Skillera PDF Generator", version="1.0.0")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "pdf-generator"
    }

@app.get("/")
def root():
    return {"message": "Skillera PDF Generator API"}