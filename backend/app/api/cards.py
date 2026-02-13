"""
Sprint 1: Cards API
Endpoints for managing CardProducts and UserCards
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import CardProduct, UserCard, RewardRule

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/card-products", response_model=List[Dict[str, Any]])
def get_card_products(session: Session = Depends(get_session)):
    """
    Get all card products from the master library with their reward rules.
    
    Sprint 1: Returns CardProducts (not user-specific instances).
    Used for card discovery and identification.
    
    Returns:
        List of CardProducts with their reward rules
    """
    try:
        # Get all card products
        products_statement = select(CardProduct).where(
            CardProduct.is_available_in_market == True
        ).order_by(CardProduct.provider, CardProduct.card_name)
        products = session.exec(products_statement).all()
        
        result = []
        for product in products:
            # Get reward rules for this card product
            rules_statement = select(RewardRule).where(
                RewardRule.card_product_id == product.id
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
            
            product_data = {
                "id": str(product.id),
                "provider": product.provider,
                "card_name": product.card_name,
                "base_reward_rate": float(product.base_reward_rate),
                "image_url": product.image_url,
                "benefits_url": product.benefits_url,
                "reward_rules": reward_rules
            }
            
            result.append(product_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch card products: {str(e)}"
        )


@router.get("/user-cards/unidentified", response_model=List[Dict[str, Any]])
def get_unidentified_cards(
    user_id: UUID = Query(..., description="User ID to filter by"),
    session: Session = Depends(get_session)
):
    """
    Get user's Plaid-synced cards that haven't been identified yet.
    
    Sprint 1: Returns UserCards where card_product_id is NULL.
    These are cards synced from Plaid that the user needs to identify.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        List of unidentified UserCards
    """
    try:
        # Get unidentified user cards
        statement = select(UserCard).where(
            UserCard.user_id == user_id,
            UserCard.card_product_id == None,
            UserCard.is_active == True
        ).order_by(UserCard.created_at)
        
        user_cards = session.exec(statement).all()
        
        result = [
            {
                "id": str(card.id),
                "plaid_account_id": card.plaid_account_id,
                "official_name": card.official_name,
                "mask": card.mask,
                "created_at": card.created_at.isoformat()
            }
            for card in user_cards
        ]
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch unidentified cards: {str(e)}"
        )


@router.post("/user-cards/{user_card_id}/identify")
async def identify_user_card(
    user_card_id: UUID,
    card_product_id: UUID = Query(..., description="CardProduct ID to link to"),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Identify a user's Plaid-synced card as a specific card product.
    
    Sprint 1: Core endpoint for card identification flow.
    User says "my Plaid account x1234 is a Chase Freedom Unlimited"
    
    Args:
        user_card_id: UUID of the UserCard to identify
        card_product_id: UUID of the CardProduct to link to
        
    Returns:
        Success message with card details
    """
    try:
        # Get UserCard
        user_card = session.exec(
            select(UserCard).where(UserCard.id == user_card_id)
        ).first()
        
        if not user_card:
            raise HTTPException(status_code=404, detail="UserCard not found")
        
        # Verify CardProduct exists
        card_product = session.exec(
            select(CardProduct).where(CardProduct.id == card_product_id)
        ).first()
        
        if not card_product:
            raise HTTPException(status_code=404, detail="CardProduct not found")
        
        # Link them
        user_card.card_product_id = card_product_id
        user_card.identified_at = datetime.utcnow()
        user_card.updated_at = datetime.utcnow()
        
        session.commit()
        session.refresh(user_card)
        
        return {
            "status": "success",
            "user_card_id": str(user_card.id),
            "card_product": f"{card_product.provider} {card_product.card_name}",
            "message": f"Successfully identified as {card_product.provider} {card_product.card_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to identify card: {str(e)}"
        )
