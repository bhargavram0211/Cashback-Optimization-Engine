"""
Cashback Optimization Engine - Reports Router
Consolidated endpoints for comprehensive analytics reports
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.services.analytics import AnalyticsService
from app.schemas import (
    SavingsReport,
    SavingsSummary,
    CategoryBreakdown,
    RecommendedCard
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/savings/{user_id}", response_model=SavingsReport)
async def get_savings_report(user_id: str, session: Session = Depends(get_session)):
    """
    Get a comprehensive savings report for a user.
    
    This endpoint consolidates multiple analytics queries into a single response:
    - Summary: Total spending, earnings, and opportunity cost
    - Category Breakdown: Spending patterns by category
    - Top Recommendation: Best card to add to maximize rewards
    
    This is the primary endpoint for dashboard views and user reports.
    
    Args:
        user_id: UUID of the user
        session: Database session (injected)
    
    Returns:
        SavingsReport with summary, category breakdown, and top recommendation
    
    Raises:
        404: No transactions found for this user
        400: Invalid user_id format
        500: Database or processing error
    
    Example Response:
    {
        "summary": {
            "total_spent": 50384.0,
            "total_lost_savings": 611.86,
            "total_earned": 503.96,
            "transaction_count": 121,
            "total_potential": 1115.82
        },
        "category_breakdown": [
            {
                "category": "DINING",
                "transaction_count": 24,
                "total_spent": 12000.0,
                "lost_savings": 240.0,
                "actual_cashback": 120.0,
                "potential_cashback": 360.0
            },
            ...
        ],
        "top_recommendation": {
            "provider": "Chase",
            "card_name": "Freedom Unlimited",
            "times_recommended": 97,
            "total_potential_savings": 371.86,
            "avg_savings_per_transaction": 3.83
        }
    }
    """
    try:
        # Fetch summary
        summary_data = AnalyticsService.get_savings_summary(session, user_id)
        if not summary_data:
            raise HTTPException(
                status_code=404,
                detail=f"No transactions found for user {user_id}"
            )
        
        # Fetch category breakdown
        breakdown_data = AnalyticsService.get_category_breakdown(session, user_id)
        if not breakdown_data:
            raise HTTPException(
                status_code=404,
                detail=f"No category data found for user {user_id}"
            )
        
        # Fetch top recommendation (may be None if no recommendations exist)
        recommendation_data = AnalyticsService.get_top_recommendation(session, user_id)
        
        # Build the consolidated report
        report = SavingsReport(
            summary=SavingsSummary(**summary_data),
            category_breakdown=[CategoryBreakdown(**item) for item in breakdown_data],
            top_recommendation=RecommendedCard(**recommendation_data) if recommendation_data else None
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user_id format: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate savings report: {str(e)}"
        )

