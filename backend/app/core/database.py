import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Fallback to SQLite if PostgreSQL connection is unavailable locally
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        # Test connection
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print(f"[Database Warning] Could not connect to PostgreSQL ({e}). Falling back to SQLite local database (bhoomisetu.db)...")
        sqlite_url = "sqlite:///./bhoomisetu.db"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
