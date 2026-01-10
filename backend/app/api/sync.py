"""
Cashback Optimization Engine - Sync API
Sub-Phase 1.4: Transaction sync endpoint with 3-stage filter pipeline

Reference: SRS Section 5.1 - Incremental Data Sync
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from pydantic import BaseModel

import plaid
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.account_type import AccountType
from plaid.model.account_subtype import AccountSubtype

from app.core import get_plaid_client_instance
from app.core.database import get_session
from app.models import PlaidItem, Card, Transaction
from app.logic import get_mapper

router = APIRouter(prefix="/sync", tags=["sync"])


# ========== Request/Response Models ==========

class SyncResponse(BaseModel):
    """Response model for sync endpoint."""
    item_id: UUID
    transactions_added: int
    transactions_updated: int
    transactions_removed: int
    accounts_synced: int
    cursor_updated: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "550e8400-e29b-41d4-a716-446655440000",
                "transactions_added": 15,
                "transactions_updated": 2,
                "transactions_removed": 0,
                "accounts_synced": 3,
                "cursor_updated": True
            }
        }


# ========== Helper Functions ==========

def is_analyzable_transaction(
    amount: float,
    primary_category: Optional[str],
    detailed_category: Optional[str]
) -> bool:
    """
    Determine if a transaction should be analyzed for cashback optimization.
    
    SRS Section 2.2: Transaction Discard/Ignore Policy
    - Returns False for:
      - Negative amounts (refunds)
      - Payments/transfers (LOAN_PAYMENTS, TRANSFER_IN, TRANSFER_OUT)
    
    Args:
        amount: Transaction amount (positive = charge, negative = refund)
        primary_category: Plaid primary category
        detailed_category: Plaid detailed category
    
    Returns:
        True if transaction should be analyzed, False otherwise
    """
    # Stage 3a: Refunds (negative amounts) are not analyzable
    if amount <= 0:
        return False
    
    # Stage 3b: Payments and transfers are not analyzable
    non_analyzable_primary = {
        "LOAN_PAYMENTS",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "LOAN_DISBURSEMENTS",
    }
    
    if primary_category in non_analyzable_primary:
        return False
    
    # All other positive transactions are analyzable
    return True


def get_credit_card_accounts(
    plaid_client: plaid.api.plaid_api.PlaidApi,
    access_token: str
) -> Dict[str, str]:
    """
    Fetch credit card accounts for a Plaid item.
    
    Returns a mapping of account_id -> official_name for credit card accounts only.
    
    Args:
        plaid_client: Initialized Plaid API client
        access_token: Plaid access token for the item
    
    Returns:
        Dictionary mapping account_id to official_name for credit card accounts
    """
    from plaid.model.accounts_get_request import AccountsGetRequest
    
    try:
        request = AccountsGetRequest(access_token=access_token)
        response = plaid_client.accounts_get(request)
        
        credit_accounts = {}
        for account in response['accounts']:
            # DEBUG: Log what we're getting from Plaid
            print(f"DEBUG: Account type={account.get('type')}, subtype={account.get('subtype')}, name={account.get('name')}")
            
            # Stage 2: Only process credit card accounts
            # Note: Plaid may return 'credit card' or 'credit_card' or enum objects
            account_type = str(account.get('type', '')).lower()
            account_subtype = str(account.get('subtype', '')).lower().replace(' ', '_')
            
            if account_type == 'credit' and 'credit' in account_subtype and 'card' in account_subtype:
                credit_accounts[account['account_id']] = account.get('official_name', account.get('name', 'Unknown'))
                print(f"DEBUG: Added credit card: {account['account_id']} - {account.get('name')}")
        
        print(f"DEBUG: Total credit accounts found: {len(credit_accounts)}")
        return credit_accounts
    
    except plaid.ApiException as e:
        raise HTTPException(status_code=500, detail=f"Plaid API error: {str(e)}")


# ========== Sync Endpoint ==========

@router.post("/{item_id}", response_model=SyncResponse)
async def sync_transactions(
    item_id: UUID,
    session: Session = Depends(get_session)
) -> SyncResponse:
    """
    Sync transactions for a Plaid item using incremental cursor-based updates.
    
    Implements the 3-Stage Filter Pipeline (SRS Section 2.2):
    - Stage 1: Discard pending transactions
    - Stage 2: Discard non-credit card accounts
    - Stage 3: Flag non-analyzable transactions (payments, transfers, refunds)
    
    Also implements:
    - UPSERT logic on plaid_transaction_id (SRS FR 1.3)
    - Cursor management (SRS FR 1.2)
    - Category normalization using NormalizationMapper
    
    Args:
        item_id: UUID of the PlaidItem to sync
        session: Database session
    
    Returns:
        SyncResponse with sync statistics
    
    Raises:
        HTTPException: If item not found or Plaid API error
    """
    # Fetch the PlaidItem from database
    statement = select(PlaidItem).where(PlaidItem.id == item_id)
    plaid_item = session.exec(statement).first()
    
    if not plaid_item:
        raise HTTPException(status_code=404, detail=f"PlaidItem {item_id} not found")
    
    # Initialize Plaid client and mapper
    plaid_client = get_plaid_client_instance()
    mapper = get_mapper()
    
    # Get credit card accounts for this item
    credit_accounts = get_credit_card_accounts(plaid_client, plaid_item.access_token)
    
    if not credit_accounts:
        return SyncResponse(
            item_id=item_id,
            transactions_added=0,
            transactions_updated=0,
            transactions_removed=0,
            accounts_synced=0,
            cursor_updated=False
        )
    
    # Ensure cards exist in database for each credit account
    card_map = {}  # account_id -> Card
    for account_id, official_name in credit_accounts.items():
        # Check if card exists
        card_statement = select(Card).where(Card.plaid_account_id == account_id)
        card = session.exec(card_statement).first()
        
        if not card:
            # Create new card
            card = Card(
                plaid_item_id=plaid_item.id,
                plaid_account_id=account_id,
                official_name=official_name,
                mask=None,  # Could extract from account details if needed
                reward_slug=None  # To be set manually by user later
            )
            session.add(card)
            session.flush()  # Get the card ID
        
        card_map[account_id] = card
    
    # Sync transactions using cursor
    cursor = plaid_item.last_cursor
    has_more = True
    transactions_added = 0
    transactions_updated = 0
    transactions_removed = 0
    
    while has_more:
        try:
            # Call Plaid transactions/sync API
            # For first sync, cursor is None and should not be passed
            if cursor:
                request = TransactionsSyncRequest(
                    access_token=plaid_item.access_token,
                    cursor=cursor
                )
            else:
                request = TransactionsSyncRequest(
                    access_token=plaid_item.access_token
                )
            response = plaid_client.transactions_sync(request)
            
            # Process added transactions
            for txn in response['added']:
                # STAGE 1: Discard pending transactions
                if txn.get('pending', False):
                    continue
                
                # STAGE 2: Only process credit card accounts
                account_id = txn.get('account_id')
                if account_id not in credit_accounts:
                    continue
                
                card = card_map[account_id]
                
                # Extract transaction data
                amount = abs(Decimal(str(txn['amount'])))
                is_positive = txn['amount'] > 0
                
                # Plaid amounts are positive for debits, but we store as positive for charges
                if not is_positive:
                    amount = -amount
                
                primary_category = txn.get('personal_finance_category', {}).get('primary')
                detailed_category = txn.get('personal_finance_category', {}).get('detailed')
                
                # STAGE 3: Determine if analyzable
                is_analyzable = is_analyzable_transaction(float(amount), primary_category, detailed_category)
                
                # Get internal bucket from mapper
                internal_bucket = mapper.get_internal_bucket(primary_category, detailed_category)
                
                # Prepare transaction data
                # Handle date: Plaid may return string or date object
                txn_date = txn['date']
                if isinstance(txn_date, str):
                    txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
                
                txn_data = {
                    "card_id": card.id,
                    "plaid_transaction_id": txn['transaction_id'],
                    "amount": amount,
                    "date": txn_date,
                    "plaid_primary_category": primary_category,
                    "plaid_detailed_category": detailed_category,
                    "internal_bucket": internal_bucket.value,  # NEW: Add mapped reward bucket
                    "merchant_name": txn.get('merchant_name') or txn.get('name'),
                    "is_analyzable": is_analyzable,
                    "updated_at": datetime.utcnow()
                }
                
                # UPSERT: Check if transaction exists
                existing_txn_statement = select(Transaction).where(
                    Transaction.plaid_transaction_id == txn['transaction_id']
                )
                existing_txn = session.exec(existing_txn_statement).first()
                
                if existing_txn:
                    # Update existing transaction
                    for key, value in txn_data.items():
                        if key != "plaid_transaction_id":  # Don't update the unique key
                            setattr(existing_txn, key, value)
                    transactions_updated += 1
                else:
                    # Insert new transaction
                    new_txn = Transaction(**txn_data)
                    session.add(new_txn)
                    transactions_added += 1
            
            # Process modified transactions (similar to added)
            for txn in response['modified']:
                # Same logic as added, but always updates
                if txn.get('pending', False):
                    continue
                
                account_id = txn.get('account_id')
                if account_id not in credit_accounts:
                    continue
                
                # Update existing transaction
                existing_txn_statement = select(Transaction).where(
                    Transaction.plaid_transaction_id == txn['transaction_id']
                )
                existing_txn = session.exec(existing_txn_statement).first()
                
                if existing_txn:
                    card = card_map[account_id]
                    amount = abs(Decimal(str(txn['amount'])))
                    is_positive = txn['amount'] > 0
                    if not is_positive:
                        amount = -amount
                    
                    primary_category = txn.get('personal_finance_category', {}).get('primary')
                    detailed_category = txn.get('personal_finance_category', {}).get('detailed')
                    is_analyzable = is_analyzable_transaction(float(amount), primary_category, detailed_category)
                    
                    # Handle date: Plaid may return string or date object
                    txn_date = txn['date']
                    if isinstance(txn_date, str):
                        txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
                    
                    existing_txn.amount = amount
                    existing_txn.date = txn_date
                    existing_txn.plaid_primary_category = primary_category
                    existing_txn.plaid_detailed_category = detailed_category
                    existing_txn.merchant_name = txn.get('merchant_name') or txn.get('name')
                    existing_txn.is_analyzable = is_analyzable
                    existing_txn.updated_at = datetime.utcnow()
                    
                    transactions_updated += 1
            
            # Process removed transactions
            for txn_id in response['removed']:
                # Delete transaction
                txn_statement = select(Transaction).where(Transaction.plaid_transaction_id == txn_id)
                txn_to_remove = session.exec(txn_statement).first()
                if txn_to_remove:
                    session.delete(txn_to_remove)
                    transactions_removed += 1
            
            # Update cursor
            cursor = response['next_cursor']
            has_more = response['has_more']
            
        except plaid.ApiException as e:
            raise HTTPException(status_code=500, detail=f"Plaid API error: {str(e)}")
    
    # Save the new cursor to the PlaidItem
    plaid_item.last_cursor = cursor
    plaid_item.updated_at = datetime.utcnow()
    
    # Commit all changes
    session.commit()
    
    return SyncResponse(
        item_id=item_id,
        transactions_added=transactions_added,
        transactions_updated=transactions_updated,
        transactions_removed=transactions_removed,
        accounts_synced=len(credit_accounts),
        cursor_updated=True
    )

