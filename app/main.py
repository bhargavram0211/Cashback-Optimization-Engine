"""
Cashback Optimization Engine - Main Application
Sub-Phase 1.2: Added data models and table initialization
"""

import os
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel, create_engine, text
from typing import Dict

# Import models to register them with SQLModel metadata
from app.models import User, PlaidItem, Card, Transaction

# Initialize FastAPI app
app = FastAPI(
    title="Cashback Optimization Engine",
    description="Backend API for credit card cashback optimization",
    version="0.2.0"
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cashback_user:cashback_pass_local_dev_only@db:5432/cashback_db")

# Create engine (lazy connection, won't connect until first query)
engine = create_engine(DATABASE_URL, echo=True)


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Health check endpoint to verify backend is running.
    """
    return {"status": "Backend is Online"}


@app.get("/db-test")
async def db_test() -> Dict[str, str]:
    """
    Database connectivity test endpoint.
    Attempts to connect to PostgreSQL and execute a simple query.
    """
    try:
        with Session(engine) as session:
            # Execute a simple query to verify connection
            result = session.exec(text("SELECT 1 as test")).first()
            if result:
                return {"status": "Database Connected"}
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Database query returned no results"
                )
    except Exception as e:
        # Return the specific error message for debugging
        return {
            "status": "Database Connection Failed",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.on_event("startup")
async def startup_event():
    """
    Runs on application startup.
    Creates all database tables if they don't exist.
    """
    print("🚀 Cashback Optimization Engine - Backend Starting...")
    print(f"📊 Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not Set'}")
    
    # Create all tables in the database
    print("📦 Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables ready!")
    print(f"   - Tables: users, plaid_items, cards, transactions")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs on application shutdown.
    """
    print("👋 Cashback Optimization Engine - Backend Shutting Down...")
    engine.dispose()

