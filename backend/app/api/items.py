"""
API endpoints for PlaidItem management (testing/development)
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.models import PlaidItem, User, UserCard, Transaction
from app.core.database import get_session
from app.api.auth import get_current_user

router = APIRouter(prefix="/items", tags=["items"])


class PlaidItemCreate(BaseModel):
    """Request model for creating a PlaidItem"""
    user_id: UUID
    access_token: str
    institution_id: Optional[str] = None
    

class PlaidItemResponse(BaseModel):
    """Response model for PlaidItem data"""
    id: UUID
    user_id: UUID
    institution_id: Optional[str]
    last_cursor: Optional[str]
    created_at: datetime
    updated_at: datetime
    

@router.post("", response_model=PlaidItemResponse, status_code=201)
def create_plaid_item(
    item_data: PlaidItemCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new PlaidItem (bank connection).
    
    For testing/development. In production, this would be created
    via Plaid Link flow.
    
    Args:
        item_data: User ID and Plaid access token
        session: Database session
        
    Returns:
        Created PlaidItem with ID and timestamps
        
    Example:
        POST /items
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "access_token": "access-sandbox-abc123...",
            "institution_id": "ins_3"
        }
        
        Response:
        {
            "id": "660e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "institution_id": "ins_3",
            "last_cursor": null,
            "created_at": "2026-01-04T12:00:00",
            "updated_at": "2026-01-04T12:00:00"
        }
    """
    # Verify user exists
    user = session.get(User, item_data.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {item_data.user_id} not found"
        )
    
    # Create new PlaidItem
    item = PlaidItem(
        user_id=item_data.user_id,
        access_token=item_data.access_token,
        institution_id=item_data.institution_id,
        last_cursor=None
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return PlaidItemResponse(
        id=item.id,
        user_id=item.user_id,
        institution_id=item.institution_id,
        last_cursor=item.last_cursor,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.get("/{item_id}", response_model=PlaidItemResponse)
def get_plaid_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a PlaidItem by ID.
    
    Requires: Authorization header with Bearer token
    Only returns items owned by the authenticated user.
    
    Args:
        item_id: UUID of the PlaidItem
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        PlaidItem data (access_token hidden)
        
    Raises:
        404: Item not found
        403: User doesn't own this item
    """
    item = session.get(PlaidItem, item_id)
    
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"PlaidItem {item_id} not found"
        )
    
    # Verify ownership
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this bank connection"
        )
    
    return PlaidItemResponse(
        id=item.id,
        user_id=item.user_id,
        institution_id=item.institution_id,
        last_cursor=item.last_cursor,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.get("", response_model=list[PlaidItemResponse])
def list_plaid_items(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    List PlaidItems for the authenticated user.
    
    Requires: Authorization header with Bearer token
    Only returns items owned by the authenticated user.
    
    Args:
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        List of PlaidItems owned by the user
    """
    query = select(PlaidItem).where(PlaidItem.user_id == current_user.id)
    items = session.exec(query).all()
    
    return [
        PlaidItemResponse(
            id=item.id,
            user_id=item.user_id,
            institution_id=item.institution_id,
            last_cursor=item.last_cursor,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in items
    ]


@router.delete("/{item_id}", status_code=204)
def delete_plaid_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    response: Response = None
):
    """
    Delete a PlaidItem (remove bank connection).
    
    Only the owner of the item can delete it.
    This will also delete all associated UserCards and Transactions.
    
    Args:
        item_id: UUID of the PlaidItem to delete
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        204 No Content on success
        
    Raises:
        404: Item not found
        403: User doesn't own this item
        500: Database error during deletion
    """
    try:
        item = session.get(PlaidItem, item_id)
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"PlaidItem {item_id} not found"
            )
        
        # Verify ownership
        if item.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this bank connection"
            )
        
        # Delete related records first (cascading delete)
        # 1. Find all UserCards associated with this PlaidItem
        user_cards = session.exec(
            select(UserCard).where(UserCard.plaid_item_id == item_id)
        ).all()
        
        if user_cards:
            user_card_ids = [uc.id for uc in user_cards]
            
            # 2. Delete only transactions where user_card_id belongs to deleted bank
            # These are transactions that actually used the deleted bank's cards
            transactions_to_delete = session.exec(
                select(Transaction).where(Transaction.user_card_id.in_(user_card_ids))
            ).all()
            
            for transaction in transactions_to_delete:
                session.delete(transaction)
            
            # 3. Update transactions where best_user_card_id references deleted cards
            # These transactions belong to OTHER banks but had deleted bank's card as optimal
            # We NULL out the reference and reset optimization fields (will be recalculated)
            from decimal import Decimal
            transactions_to_update = session.exec(
                select(Transaction).where(Transaction.best_user_card_id.in_(user_card_ids))
            ).all()
            
            for transaction in transactions_to_update:
                transaction.best_user_card_id = None
                transaction.best_possible_cashback = None
                transaction.lost_savings = Decimal("0.0")
                # Note: We keep market_winner_product_id as it references CardProduct, not UserCard
                session.add(transaction)
            
            # Flush to ensure transactions are deleted/updated before we delete UserCards
            session.flush()
            
            # 4. Delete all UserCards
            for user_card in user_cards:
                session.delete(user_card)
            
            # Flush to ensure UserCards are deleted before we delete PlaidItem
            session.flush()
        
        # 5. Finally, delete the PlaidItem
        session.delete(item)
        session.commit()
        
        # 6. Re-optimize remaining transactions for this user
        # This recalculates best_user_card_id for transactions that had it NULLed out
        try:
            from app.services.optimizer import optimize_user_transactions
            optimize_user_transactions(session, current_user.id)
            print(f"✅ Re-optimized transactions for user {current_user.id} after bank deletion")
        except Exception as e:
            # Log error but don't fail the deletion
            print(f"⚠️  Failed to re-optimize transactions after bank deletion: {e}")
            # Continue - deletion was successful, optimization can be done manually
        
        # Return 204 No Content explicitly
        return Response(status_code=204)
    except HTTPException:
        # Re-raise HTTP exceptions (404, 403, etc.)
        raise
    except Exception as e:
        # Rollback on any other error
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting bank connection: {str(e)}"
        )

