"""
Cashback Optimization Engine - Data Models
Sub-Phase 1.2: SQLModel table definitions
Phase 2.1: Card & Rules Registry

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
    
    Phase 2.1: Added provider, card_name, and base_reward_rate for reward calculation.
    """
    __tablename__ = "cards"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    plaid_item_id: UUID = Field(foreign_key="plaid_items.id", nullable=False, index=True)
    plaid_account_id: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    official_name: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    mask: Optional[str] = Field(default=None, sa_column=Column(String(10)))
    
    # Card identification (Phase 2.1)
    provider: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100)),
        description="Card issuer (e.g., 'Chase', 'American Express', 'Capital One')"
    )
    card_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(200)),
        description="Card product name (e.g., 'Sapphire Reserve', 'Gold Card')"
    )
    
    # Reward configuration
    reward_slug: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100)),
        description="Identifier for reward rules (e.g., 'chase_sapphire', 'amex_gold')"
    )
    base_reward_rate: Decimal = Field(
        default=Decimal("1.0"),
        sa_column=Column(DECIMAL(5, 2), nullable=False),
        description="Base cashback rate (e.g., 1.0 for 1%, 1.5 for 1.5%)"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RewardRule(SQLModel, table=True):
    """
    Reward multipliers for specific spending categories per card.
    
    Phase 2.1: Defines category-specific reward rates (e.g., 3x on dining, 2x on gas).
    Each card can have multiple reward rules, one per bucket.
    
    Example:
    - Chase Sapphire Reserve: 3x on TRAVEL, 3x on DINING
    - Amex Gold: 4x on DINING, 4x on GROCERY
    - Citi Double Cash: 2x on GENERAL (all purchases)
    """
    __tablename__ = "reward_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    card_id: UUID = Field(foreign_key="cards.id", nullable=False, index=True)
    
    # Reward bucket (must match internal_bucket values)
    bucket: str = Field(
        sa_column=Column(String(50), nullable=False, index=True),
        description="Internal reward bucket (DINING, GROCERY, GAS, TRAVEL, etc.)"
    )
    
    # Reward multiplier
    multiplier: Decimal = Field(
        sa_column=Column(DECIMAL(5, 2), nullable=False),
        description="Cashback multiplier (e.g., 3.0 for 3x, 1.5 for 1.5x)"
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
    
    # Internal reward bucket mapping (from NormalizationMapper)
    internal_bucket: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), index=True),
        description="Mapped reward bucket (DINING, GROCERY, GAS, etc.) from mapper"
    )
    
    # Merchant info
    merchant_name: Optional[str] = Field(default=None, sa_column=Column(String(500)))
    
    # Analysis flags
    is_analyzable: bool = Field(
        default=True,
        description="False for refunds, payments, transfers per SRS Section 2.2"
    )
    
    # Optimization results (to be populated by optimization engine - Phase 2.1+)
    actual_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Cashback earned on the card used"
    )
    best_card_id: Optional[UUID] = Field(
        default=None,
        foreign_key="cards.id",
        description="Card that would have yielded highest rewards"
    )
    best_possible_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Maximum possible cashback from best card"
    )
    lost_savings: Decimal = Field(
        default=Decimal("0.0"),
        sa_column=Column(DECIMAL(10, 2), nullable=False),
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
RewardRule.model_rebuild()
Transaction.model_rebuild()

