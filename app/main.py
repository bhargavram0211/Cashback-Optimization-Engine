"""
Cashback Optimization Engine - Main Application
Sub-Phase 1.3: Added category normalization mapper
"""

import os
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel, create_engine, text
from typing import Dict, Optional
from pydantic import BaseModel

# Import models to register them with SQLModel metadata
from app.models import User, PlaidItem, Card, Transaction

# Import category mapper
from app.logic import get_mapper, RewardBucket

# Initialize FastAPI app
app = FastAPI(
    title="Cashback Optimization Engine",
    description="Backend API for credit card cashback optimization",
    version="0.3.0"
)


# ========== Request/Response Models ==========

class CategoryMapRequest(BaseModel):
    """Request model for category mapping test endpoint."""
    primary_category: Optional[str] = None
    detailed_category: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "primary_category": "FOOD_AND_DRINK",
                "detailed_category": "FOOD_AND_DRINK_RESTAURANT"
            }
        }


class CategoryMapResponse(BaseModel):
    """Response model for category mapping test endpoint."""
    primary_category: Optional[str]
    detailed_category: Optional[str]
    internal_bucket: str
    tier_used: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "primary_category": "FOOD_AND_DRINK",
                "detailed_category": "FOOD_AND_DRINK_RESTAURANT",
                "internal_bucket": "DINING",
                "tier_used": "detailed"
            }
        }

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


@app.post("/test-map", response_model=CategoryMapResponse)
async def test_category_mapping(request: CategoryMapRequest) -> CategoryMapResponse:
    """
    Test endpoint for category normalization mapper.
    
    Maps Plaid's PFCv2 categories to internal reward buckets using 3-tier fallback:
    - Tier 1: Detailed category match
    - Tier 2: Primary category fallback
    - Tier 3: GENERAL default
    
    This endpoint is temporary for Sub-Phase 1.3 testing.
    
    Args:
        request: CategoryMapRequest with primary and/or detailed categories
    
    Returns:
        CategoryMapResponse with the mapped bucket and tier used
    
    Example:
        POST /test-map
        {
            "primary_category": "FOOD_AND_DRINK",
            "detailed_category": "FOOD_AND_DRINK_RESTAURANT"
        }
        
        Response:
        {
            "primary_category": "FOOD_AND_DRINK",
            "detailed_category": "FOOD_AND_DRINK_RESTAURANT",
            "internal_bucket": "DINING",
            "tier_used": "detailed"
        }
    """
    mapper = get_mapper()
    
    # Get the mapped bucket
    bucket = mapper.get_internal_bucket(
        primary_category=request.primary_category,
        detailed_category=request.detailed_category
    )
    
    # Determine which tier was used
    tier_used = "general"  # Default
    
    if request.detailed_category and request.detailed_category in mapper.detailed_to_bucket:
        tier_used = "detailed"
    elif request.primary_category and request.primary_category in mapper.primary_to_bucket:
        tier_used = "primary"
    
    return CategoryMapResponse(
        primary_category=request.primary_category,
        detailed_category=request.detailed_category,
        internal_bucket=bucket.value,
        tier_used=tier_used
    )


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
    
    # Initialize category mapper
    print("🗺️  Initializing category mapper...")
    mapper = get_mapper()
    print(f"✅ Category mapper ready: {mapper}")
    print(f"   - Bucket stats: {mapper.get_bucket_stats()}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs on application shutdown.
    """
    print("👋 Cashback Optimization Engine - Backend Shutting Down...")
    engine.dispose()

