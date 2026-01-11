"""
Phase 3.2: Cards API
Endpoints for fetching card information and reward structures
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import Card, RewardRule

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=List[Dict[str, Any]])
def get_all_cards(session: Session = Depends(get_session)):
    """
    Get all cards with their reward rules.
    
    Phase 3.2: Returns all 10 cards (4 wallet + 6 market) with their reward structures
    for the Card Discovery page.
    
    Returns:
        List of cards with their reward rules
    """
    try:
        # Get all cards
        cards_statement = select(Card).order_by(Card.is_in_user_wallet.desc(), Card.provider)
        cards = session.exec(cards_statement).all()
        
        result = []
        for card in cards:
            # Get reward rules for this card
            rules_statement = select(RewardRule).where(
                RewardRule.card_id == card.id
            ).order_by(RewardRule.multiplier.desc())
            rules = session.exec(rules_statement).all()
            
            # Format reward rules
            reward_rules = [
                {
                    "bucket": rule.bucket,
                    "multiplier": float(rule.multiplier)
                }
                for rule in rules
            ]
            
            card_data = {
                "id": str(card.id),
                "provider": card.provider,
                "card_name": card.card_name,
                "base_reward_rate": float(card.base_reward_rate),
                "is_in_user_wallet": card.is_in_user_wallet,
                "image_url": card.image_url,
                "reward_rules": reward_rules
            }
            
            result.append(card_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch cards: {str(e)}"
        )
