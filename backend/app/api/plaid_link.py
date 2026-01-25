"""
Cashback Optimization Engine - Plaid Link API
Sprint 2: Plaid Link token creation and public token exchange
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID

from app.models.models import User, PlaidItem
from app.core.database import get_session
from app.core.plaid import get_plaid_client_instance
from app.api.auth import get_current_user
from app.api.sync import sync_transactions

import plaid
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest

router = APIRouter(prefix="/plaid", tags=["plaid-link"])


# Request/Response Models
class LinkTokenResponse(BaseModel):
    """Plaid Link token response"""
    link_token: str
    expiration: str


class ExchangeTokenRequest(BaseModel):
    """Public token exchange request"""
    public_token: str
    institution_id: str
    institution_name: str


class ExchangeTokenResponse(BaseModel):
    """Token exchange response"""
    plaid_item_id: str
    institution_name: str
    transactions_synced: int
    cards_found: int
    message: str


@router.post("/create-link-token", response_model=LinkTokenResponse)
async def create_link_token(
    current_user: User = Depends(get_current_user)
):
    """
    Create a Plaid Link token for initiating the Link flow.
    
    This token is used to initialize Plaid Link UI, allowing users
    to connect their bank accounts.
    
    Requires: Authorization header with Bearer token
    
    Returns:
        link_token: Token to initialize Plaid Link
        expiration: When the token expires
        
    Raises:
        500: Plaid API error
    """
    try:
        plaid_client = get_plaid_client_instance()
        
        # Create link token request
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(
                client_user_id=str(current_user.id)
            ),
            client_name="Cashback Optimization Engine",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )
        
        # Call Plaid API
        response = plaid_client.link_token_create(request)
        
        return LinkTokenResponse(
            link_token=response.link_token,
            expiration=response.expiration.isoformat()
        )
        
    except plaid.ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Plaid API error: {e.body}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating link token: {str(e)}"
        )


@router.post("/exchange-token", response_model=ExchangeTokenResponse)
async def exchange_public_token(
    exchange_data: ExchangeTokenRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Exchange Plaid public_token for access_token.
    
    This is called after the user successfully connects their bank
    via Plaid Link. The public_token is exchanged for an access_token,
    which is stored and used for future API calls.
    
    After exchange, automatically:
    1. Creates PlaidItem
    2. Syncs transactions
    
    Requires: Authorization header with Bearer token
    
    Args:
        exchange_data: public_token and institution info from Plaid Link
        
    Returns:
        PlaidItem info and sync results
        
    Raises:
        500: Plaid API error
    """
    try:
        plaid_client = get_plaid_client_instance()
        
        # Exchange public token for access token
        request = ItemPublicTokenExchangeRequest(
            public_token=exchange_data.public_token
        )
        response = plaid_client.item_public_token_exchange(request)
        access_token = response.access_token
        item_id = response.item_id  # Plaid's internal item_id
        
        # Create PlaidItem in our database
        plaid_item = PlaidItem(
            user_id=current_user.id,
            access_token=access_token,
            institution_id=exchange_data.institution_id,
            last_cursor=None
        )
        session.add(plaid_item)
        session.commit()
        session.refresh(plaid_item)
        
        # Automatically sync transactions
        sync_result = await sync_transactions(
            item_id=plaid_item.id,
            current_user=current_user,
            session=session
        )
        
        return ExchangeTokenResponse(
            plaid_item_id=str(plaid_item.id),
            institution_name=exchange_data.institution_name,
            transactions_synced=sync_result.transactions_added,
            cards_found=sync_result.accounts_synced,
            message=f"Successfully connected {exchange_data.institution_name}"
        )
        
    except plaid.ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Plaid API error: {e.body}"
        )
    except Exception as e:
        # Rollback if anything fails
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error exchanging token: {str(e)}"
        )


@router.post("/connect-sandbox", response_model=ExchangeTokenResponse)
async def connect_sandbox(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Connect to Plaid Sandbox for testing/onboarding.
    
    This is a helper endpoint for MVP onboarding that:
    1. Creates a PlaidItem with a sandbox access token
    2. Automatically syncs transactions
    3. Returns the sync results
    
    In production, this would be replaced by the full Plaid Link flow.
    
    Requires: Authorization header with Bearer token
    
    Returns:
        PlaidItem info and sync results
        
    Raises:
        500: Plaid API error or sync error
    """
    plaid_item = None
    
    try:
        # Check if user already has a sandbox connection
        existing_item = session.exec(
            select(PlaidItem).where(
                PlaidItem.user_id == current_user.id,
                PlaidItem.institution_id == "ins_3"  # Sandbox institution
            )
        ).first()
        
        if existing_item:
            # Already connected, just re-sync
            plaid_item = existing_item
        else:
            # Create new sandbox connection
            plaid_client = get_plaid_client_instance()
            
            # For sandbox, we need to create a sandbox token
            from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
            from plaid.model.products import Products
            
            sandbox_request = SandboxPublicTokenCreateRequest(
                institution_id="ins_3",  # Chase sandbox
                initial_products=[Products("transactions")]
            )
            
            sandbox_response = plaid_client.sandbox_public_token_create(sandbox_request)
            public_token = sandbox_response.public_token
            
            # Exchange for access token
            exchange_request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            exchange_response = plaid_client.item_public_token_exchange(exchange_request)
            access_token = exchange_response.access_token
            
            # Create PlaidItem in our database
            plaid_item = PlaidItem(
                user_id=current_user.id,
                access_token=access_token,
                institution_id="ins_3",  # Chase sandbox
                last_cursor=None
            )
            session.add(plaid_item)
            session.commit()
            session.refresh(plaid_item)
        
        # Sync transactions - this is the critical part
        # We need to ensure this completes before returning
        # For sandbox, sometimes we need to retry as Plaid generates data asynchronously
        import asyncio
        
        max_retries = 5  # Increased retries
        retry_delay = 3  # Increased delay to 3 seconds
        min_expected_transactions = 100  # Sandbox typically has 145 transactions
        sync_result = None
        
        for attempt in range(max_retries):
            try:
                sync_result = await sync_transactions(
                    item_id=plaid_item.id,
                    current_user=current_user,
                    session=session
                )
                
                # Check if we got a reasonable number of transactions for sandbox
                # Sandbox typically generates 145 transactions across 2 accounts
                if sync_result.transactions_added >= min_expected_transactions:
                    break
                    
                # If we got some transactions but not enough, wait and retry (except on last attempt)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    
            except Exception as sync_error:
                # If this is the last attempt, raise the error
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=500,
                        detail=f"PlaidItem created but sync failed after {max_retries} attempts: {str(sync_error)}"
                    )
                # Otherwise, wait and retry
                await asyncio.sleep(retry_delay)
        
        if not sync_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to sync transactions after multiple attempts"
            )
        
        message = "Re-synced existing sandbox connection" if existing_item else "Successfully connected to Plaid Sandbox"
        
        return ExchangeTokenResponse(
            plaid_item_id=str(plaid_item.id),
            institution_name="Chase (Sandbox)",
            transactions_synced=sync_result.transactions_added,
            cards_found=sync_result.accounts_synced,
            message=message
        )
        
    except plaid.ApiException as e:
        # Rollback PlaidItem creation if it was created
        if plaid_item and not existing_item:
            session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Plaid API error: {e.body}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback if anything fails
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting to sandbox: {str(e)}"
        )
