"""
Cashback Optimization Engine - Infrastructure Shell
Sub-Phase 1.1: Minimal FastAPI app with DB connectivity test
"""

import os
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, create_engine, text
from typing import Dict

# Initialize FastAPI app
app = FastAPI(
    title="Cashback Optimization Engine",
    description="Backend API for credit card cashback optimization",
    version="0.1.0"
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
    Currently just logs that the app is starting.
    """
    print("🚀 Cashback Optimization Engine - Backend Starting...")
    print(f"📊 Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not Set'}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs on application shutdown.
    """
    print("👋 Cashback Optimization Engine - Backend Shutting Down...")
    engine.dispose()

