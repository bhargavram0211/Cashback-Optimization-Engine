"""
Cashback Optimization Engine - Main Application
Sub-Phase 1.4: Added transaction sync engine
"""

import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, text
from typing import Dict, Optional
from pydantic import BaseModel

# Import models to register them with SQLModel metadata
# Sprint 1: Updated to use CardProduct and UserCard
from app.models import User, PlaidItem, CardProduct, UserCard, RewardRule, Transaction

# Import category mapper
from app.logic import get_mapper, RewardBucket

# Import core utilities
from app.core.database import engine, DATABASE_URL, get_session

# Import API routers
from app.api import sync, users, items, analytics, cards, auth, plaid_link
from app.routers import reports

# Import services
from app.services.optimizer import optimize_user_transactions
from app.api.auth import get_current_user

# Initialize FastAPI app
app = FastAPI(
    title="Cashback Optimization Engine",
    description="Backend API for credit card cashback optimization",
    version="0.4.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8501",  # Streamlit (for backward compatibility)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)  # Sprint 2: Authentication
app.include_router(plaid_link.router)  # Sprint 2: Plaid Link
app.include_router(users.router)
app.include_router(items.router)
app.include_router(sync.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(cards.router)


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

# Database engine is imported from app.core.database


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


@app.post("/optimize", tags=["Optimization"])
async def optimize(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Run the cashback optimization engine on the current user's transactions.
    
    Phase 2.2: The Optimization Engine (User-Scoped)
    
    Process:
    1. Loops through every transaction for the authenticated user
    2. For each transaction, checks the internal_bucket (e.g., DINING)
    3. Scans all cards to find which has the highest multiplier for that bucket
    4. Calculates:
       - actual_cashback: What was earned with the card used
       - best_possible_cashback: What could have been earned with optimal card
       - lost_savings: Opportunity cost (best - actual)
    5. Updates each transaction with best_card_id and lost_savings
    
    Requires: Authorization header with Bearer token
    
    Returns:
        Dict with optimization summary:
        - total_transactions: Number of transactions processed
        - optimized: Number of transactions optimized
        - skipped: Number of transactions skipped (non-analyzable, no bucket)
        - total_actual_cashback: Total cashback earned
        - total_potential_cashback: Total cashback possible
        - total_lost_savings: Total opportunity cost
        - average_lost_per_transaction: Average opportunity cost per transaction
    
    Example Response:
    {
        "status": "success",
        "total_transactions": 146,
        "optimized": 122,
        "skipped": 24,
        "total_actual_cashback": 146.00,
        "total_potential_cashback": 438.00,
        "total_lost_savings": 292.00,
        "average_lost_per_transaction": 2.39
    }
    """
    try:
        result = optimize_user_transactions(session, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """
    Runs on application startup.
    Creates all database tables if they don't exist.
    Imports card products from YAML files.
    """
    print("🚀 Cashback Optimization Engine - Backend Starting...")
    print(f"📊 Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not Set'}")
    
    # Create all tables in the database
    print("📦 Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables ready!")
    print(f"   - Tables: users, plaid_items, card_products, user_cards, reward_rules, transactions")
    
    # Import card products from YAML files
    print("📥 Importing card library...")
    try:
        from pathlib import Path
        import sys
        scripts_dir = Path(__file__).parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))
        
        # Import and run the card importer
        import import_cards
        stats = import_cards.import_all_cards(update_existing=False, verbose=False)
        
        if stats.get("failed", 0) == 0:
            print(f"✅ Card library ready: {stats['success']} cards imported, {stats['skipped']} skipped")
        else:
            print(f"⚠️  Card import completed with {stats['failed']} errors")
    except Exception as e:
        print(f"⚠️  Card import failed: {e}")
        print("   Continuing with startup...")
    
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

