# backend/app/main.py

from fastapi import FastAPI
from api import auth, documents, summary, chatbot
from db.database import init_db
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------------------------
# Initialize FastAPI app
# --------------------------------------------------------------------
app = FastAPI(title="AI-CA Backend", version="1.0.0")

# Initialize database (creates tables if not exist)
init_db()

# --------------------------------------------------------------------
# CORS Middleware (so frontend localhost:3000 can access backend)
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
# Register all API routes
# --------------------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
# app.include_router(summary.router, prefix="/summary", tags=["Summary"])
# app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])


# --------------------------------------------------------------------
# Health check route
# --------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI-CA backend is running successfully"}
