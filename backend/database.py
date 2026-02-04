from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLite database for development (default)
# To use MySQL, set DATABASE_URL in .env file:
# DATABASE_URL=mysql+pymysql://user:password@localhost/dbname
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aica.db")

# Configure engine based on database type
connect_args = {}
engine_args = {}

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    # MySQL/PostgreSQL optimizations
    engine_args = {
        "pool_pre_ping": True,  # Test connections before using them
        "pool_recycle": 3600,   # Recycle connections every hour
        "pool_size": 10,        # Connection pool size
        "max_overflow": 20      # Max extra connections
    }

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    **engine_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

