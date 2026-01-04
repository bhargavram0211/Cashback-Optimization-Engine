"""
API endpoints for PlaidItem management (testing/development)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.models import PlaidItem, User
from app.core.database import get_session

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
    session: Session = Depends(get_session)
):
    """
    Get a PlaidItem by ID.
    
    Args:
        item_id: UUID of the PlaidItem
        session: Database session
        
    Returns:
        PlaidItem data (access_token hidden)
    """
    item = session.get(PlaidItem, item_id)
    
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"PlaidItem {item_id} not found"
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
    session: Session = Depends(get_session),
    user_id: Optional[UUID] = None,
    limit: int = 10
):
    """
    List PlaidItems (for testing/development).
    
    Args:
        session: Database session
        user_id: Optional filter by user ID
        limit: Maximum number of items to return
        
    Returns:
        List of PlaidItems
    """
    query = select(PlaidItem)
    
    if user_id:
        query = query.where(PlaidItem.user_id == user_id)
    
    query = query.limit(limit)
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

