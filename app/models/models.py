"""
Cashback Optimization Engine - Data Models
Sub-Phase 1.2: SQLModel table definitions

Reference: SRS Section 3.2 - The 4-Table Model
"""

from datetime import datetime
from datetime import date as DateType
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import DECIMAL, String


class User(SQLModel, table=True):
    """
    Primary identity table.
    Represents a user of the cashback optimization system.
    """
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlaidItem(SQLModel, table=True):
    """
    Represents a bank login (Item) in Plaid.
    Each Item can contain multiple accounts (cards).
    """
    __tablename__ = "plaid_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    access_token: str = Field(sa_column=Column(String(500), nullable=False))
    institution_id: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    last_cursor: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Card(SQLModel, table=True):
    """
    Individual credit card accounts.
    Each card is linked to a PlaidItem and has a reward profile.
    """
    __tablename__ = "cards"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    plaid_item_id: UUID = Field(foreign_key="plaid_items.id", nullable=False, index=True)
    plaid_account_id: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    official_name: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    mask: Optional[str] = Field(default=None, sa_column=Column(String(10)))
    reward_slug: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100)),
        description="Identifier for reward rules (e.g., 'chase_sapphire', 'amex_gold')"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(SQLModel, table=True):
    """
    The financial ledger.
    Stores all credit card transactions with categorization and analyzability flags.
    
    Key Fields:
    - plaid_transaction_id: Unique identifier from Plaid (natural key for idempotent upserts)
    - is_analyzable: False for refunds, payments, transfers (filtered per SRS Section 2.2)
    - amount: Stored as Decimal(12,2) for precise financial calculations
    """
    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    card_id: UUID = Field(foreign_key="cards.id", nullable=False, index=True)
    
    # Plaid natural key for idempotency (UNIQUE CONSTRAINT per SRS requirements)
    plaid_transaction_id: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False, index=True),
        description="Unique identifier from Plaid API for idempotent upserts"
    )
    
    # Financial data
    amount: Decimal = Field(
        sa_column=Column(DECIMAL(12, 2), nullable=False),
        description="Transaction amount (positive for charges, negative for refunds)"
    )
    date: DateType = Field(nullable=False, index=True)
    
    # Plaid categorization (PFCv2)
    plaid_primary_category: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    plaid_detailed_category: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    
    # Merchant info
    merchant_name: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    
    # Analysis flags
    is_analyzable: bool = Field(
        default=True,
        description="False for refunds, payments, transfers per SRS Section 2.2"
    )
    
    # Optimization results (to be populated by optimization engine)
    actual_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Cashback earned on the card used"
    )
    best_card_id: Optional[UUID] = Field(
        default=None,
        description="Card that would have yielded highest rewards"
    )
    best_possible_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Maximum possible cashback from best card"
    )
    lost_savings: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Opportunity cost (best_possible - actual)"
    )
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Force Pydantic to resolve all forward references after all classes are defined
# This prevents RecursionError in Pydantic v2's _repr logic
User.model_rebuild()
PlaidItem.model_rebuild()
Card.model_rebuild()
Transaction.model_rebuild()
