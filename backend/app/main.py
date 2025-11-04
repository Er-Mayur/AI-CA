# backend/app/main.py

from fastapi import FastAPI
from api import auth, documents, summary, chatbot
from db.database import init_db
from fastapi.middleware.cors import CORSMiddleware
import subprocess, requests, time


# --------------------------------------------------------------------
# 🔹 Ensure Ollama Server is Running (for local LLM)
# --------------------------------------------------------------------
def ensure_ollama_running():
    """Check if Ollama is running; if not, start it in background."""
    OLLAMA_URL = "http://127.0.0.1:11434/api/version"
    try:
        res = requests.get(OLLAMA_URL, timeout=2)
        if res.status_code == 200:
            print("✅ Ollama server already running.")
            return
    except Exception:
        print("🚀 Ollama not running — starting now...")

    # Start Ollama in background (no console spam)
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait a few seconds for server boot
    for i in range(10):
        try:
            res = requests.get(OLLAMA_URL, timeout=2)
            if res.status_code == 200:
                print("✅ Ollama server started successfully.")
                return
        except Exception:
            time.sleep(1)

    print("⚠️ Warning: Ollama did not respond after 10s — check manually.")


# --------------------------------------------------------------------
# 🔹 Initialize FastAPI app
# --------------------------------------------------------------------
app = FastAPI(title="AI-CA Backend", version="1.0.0")

# Initialize database (creates tables if not exist)
init_db()


# --------------------------------------------------------------------
# 🔹 CORS Middleware (for frontend access)
# --------------------------------------------------------------------
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------
# 🔹 Register all API routes
# --------------------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(summary.router, prefix="/summary", tags=["Summary"])
# app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])


# --------------------------------------------------------------------
# 🔹 Startup Event: Ensure Ollama & AI Models
# --------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    ensure_ollama_running()
    print("🚀 AI-CA backend started — local Mistral LLM ready.")


# --------------------------------------------------------------------
# 🔹 Health check route
# --------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI-CA backend is running successfully"}
