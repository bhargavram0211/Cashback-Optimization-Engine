"""
GetCardIQ - Pydantic Schemas
Response models for API endpoints
"""

from pydantic import BaseModel
from typing import List, Dict, Optional
from decimal import Decimal


class CategoryBreakdown(BaseModel):
    """Breakdown of spending and opportunity cost for a single category."""
    category: str
    transaction_count: int
    total_spent: float
    lost_savings: float
    actual_cashback: float
    potential_cashback: float


class RecommendedCard(BaseModel):
    """Details about the top recommended card."""
    provider: str
    card_name: str
    times_recommended: int
    total_potential_savings: float
    avg_savings_per_transaction: float


class SavingsSummary(BaseModel):
    """Aggregate spending and cashback metrics."""
    total_spent: float
    total_lost_savings: float
    total_earned: float
    transaction_count: int
    total_potential: float


class SavingsReport(BaseModel):
    """
    Comprehensive savings report combining summary, category breakdown, and recommendations.
    
    This is the primary response model for the consolidated savings report endpoint.
    """
    summary: SavingsSummary
    category_breakdown: List[CategoryBreakdown]
    top_recommendation: Optional[RecommendedCard]
    
    class Config:
        json_schema_extra = {
            "example": {
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
                    }
                ],
                "top_recommendation": {
                    "provider": "Chase",
                    "card_name": "Freedom Unlimited",
                    "times_recommended": 97,
                    "total_potential_savings": 371.86,
                    "avg_savings_per_transaction": 3.83
                }
            }
        }

