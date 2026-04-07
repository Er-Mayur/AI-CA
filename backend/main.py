import os
import warnings

# Suppress known non-fatal SSL compatibility warning on macOS system Python.
warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL 1.1.1+",
)

# Disable Chroma/PostHog telemetry globally for API runtime.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")
os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "FALSE")
os.environ.setdefault("POSTHOG_DISABLED", "true")

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import uvicorn

from database import engine, get_db
from models import Base
from routers import auth, documents, tax, dashboard, qna, investments, admin

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-CA: AI-Powered Virtual Chartered Accountant",
    description="AI-driven tax computation and compliance dashboard for Indian income tax",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(tax.router, prefix="/api/tax", tags=["Tax Calculation"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(qna.router, prefix="/api/qna", tags=["Q&A"])
app.include_router(investments.router, prefix="/api/investments", tags=["Investments"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])

@app.get("/")
def read_root():
    return {
        "message": "AI-CA: AI-Powered Virtual Chartered Accountant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

