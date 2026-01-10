"""
Cashback Optimization Engine - Analytics API
Endpoints for aggregate insights and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Dict, Any

from app.core.database import get_session
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary/{user_id}", response_model=Dict[str, Any])
async def get_savings_summary(user_id: str, session: Session = Depends(get_session)):
    """
    Get aggregate spending and opportunity cost summary for a user.
    
    Returns:
        - total_spent: Total amount spent across all transactions
        - total_lost_savings: Total opportunity cost (money left on the table)
        - total_earned: Actual cashback earned
        - total_potential: Maximum possible cashback if optimal cards were used
        - transaction_count: Number of analyzable transactions
    """
    try:
        summary = AnalyticsService.get_savings_summary(session, user_id)
        if not summary:
            raise HTTPException(
                status_code=404, 
                detail="No transactions found for this user."
            )
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user_id: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get savings summary: {str(e)}"
        )


@router.get("/category-breakdown/{user_id}", response_model=List[Dict[str, Any]])
async def get_category_breakdown(user_id: str, session: Session = Depends(get_session)):
    """
    Get spending and opportunity cost breakdown by category.
    
    Returns a list of categories sorted by lost_savings (descending),
    showing where the user is missing the most rewards.
    """
    try:
        breakdown = AnalyticsService.get_category_breakdown(session, user_id)
        if not breakdown:
            raise HTTPException(
                status_code=404, 
                detail="No transactions found for this user."
            )
        return breakdown
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user_id: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get category breakdown: {str(e)}"
        )


@router.get("/top-recommendation/{user_id}", response_model=Dict[str, Any])
async def get_top_recommendation(user_id: str, session: Session = Depends(get_session)):
    """
    Get the single best card recommendation for the user.
    
    Returns the card that would save the most money if the user
    switched to using it for the transactions where it's optimal.
    """
    try:
        recommendation = AnalyticsService.get_top_recommendation(session, user_id)
        if not recommendation:
            raise HTTPException(
                status_code=404, 
                detail="No recommendations found for this user."
            )
        return recommendation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user_id: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get top recommendation: {str(e)}"
        )


@router.get("/card-comparison/{user_id}", response_model=List[Dict[str, Any]])
async def get_card_performance_comparison(user_id: str, session: Session = Depends(get_session)):
    """
    Compare all cards and show potential savings for each.
    
    Returns a list of cards sorted by potential_savings (descending),
    showing which cards would be most valuable to add to the wallet.
    """
    try:
        comparison = AnalyticsService.get_card_performance_comparison(session, user_id)
        if not comparison:
            raise HTTPException(
                status_code=404, 
                detail="No card recommendations found for this user."
            )
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user_id: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get card comparison: {str(e)}"
        )

