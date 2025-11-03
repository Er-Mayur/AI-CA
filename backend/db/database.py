# backend/app/db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# --------------------------------------------------------------------
# 1️ Database URL — change to Postgres easily later
# --------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aica.db")

# --------------------------------------------------------------------
# 2️ SQLAlchemy Base class
# --------------------------------------------------------------------
class Base(DeclarativeBase):
    pass

# --------------------------------------------------------------------
# 3️⃣ Create engine
# --------------------------------------------------------------------
# For SQLite we need special flag for multithreading
engine_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=engine_args)

# --------------------------------------------------------------------
# 4️⃣ Create SessionLocal for dependency injection
# --------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --------------------------------------------------------------------
# 5️⃣ Function to initialize tables
# --------------------------------------------------------------------
def init_db():
    """Import models and create tables."""
    from db import models  # Import here to avoid circular import
    Base.metadata.create_all(bind=engine)

# --------------------------------------------------------------------
# 6️ Dependency for FastAPI routes
# --------------------------------------------------------------------
def get_db():
    """Yields a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
