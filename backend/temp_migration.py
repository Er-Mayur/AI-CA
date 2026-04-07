import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SQLALCHEMY_DATABASE_URL as DATABASE_URL

def run_migration():
    """
    Connects to the database and updates the verification_status column
    to be lowercase to match the Pydantic enum validation.
    """
    if "sqlite" in DATABASE_URL:
        print("Database is SQLite. No migration needed as the file is recreated.")
        return

    print(f"Connecting to database: {DATABASE_URL.replace('mysql+pymysql://', 'mysql://****:****@')}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Starting data migration for 'documents' table...")
        
        # Using text() to construct a safe SQL query
        update_query = text("""
            UPDATE documents 
            SET verification_status = LOWER(verification_status) 
            WHERE verification_status IN ('PENDING', 'VERIFIED', 'FAILED');
        """)
        
        result = db.execute(update_query)
        db.commit()
        
        print(f"Migration complete. {result.rowcount} rows affected.")
        
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        db.rollback()
    finally:
        db.close()
        print("Database connection closed.")

if __name__ == "__main__":
    run_migration()
