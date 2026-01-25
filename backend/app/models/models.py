"""
Cashback Optimization Engine - Data Models
Sub-Phase 1.2: SQLModel table definitions
Phase 2.1: Card & Rules Registry
Sprint 1: CardProduct + UserCard Architecture

Reference: SRS Section 3.2 - Refactored to separate card products from user instances
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
    
    Sprint 2: Added password authentication and onboarding tracking.
    """
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    password_hash: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="Bcrypt hash of user's password"
    )
    name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255)),
        description="User's display name"
    )
    onboarding_completed: bool = Field(
        default=False,
        description="Whether user has completed initial onboarding flow"
    )
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


class CardProduct(SQLModel, table=True):
    """
    Master library of credit card products.
    Defines card types and their reward structures.
    
    Sprint 1: This is the shared library that all users reference.
    Examples: Chase Freedom Unlimited, Amex Gold, etc.
    """
    __tablename__ = "card_products"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    provider: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="Card issuer (e.g., 'Chase', 'American Express', 'Capital One')"
    )
    card_name: str = Field(
        sa_column=Column(String(200), nullable=False),
        description="Card product name (e.g., 'Freedom Unlimited', 'Gold Card')"
    )
    base_reward_rate: Decimal = Field(
        default=Decimal("1.0"),
        sa_column=Column(DECIMAL(5, 2), nullable=False),
        description="Base cashback rate (e.g., 1.0 for 1%, 1.5 for 1.5%)"
    )
    image_url: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500)),
        description="URL to card image"
    )
    benefits_url: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500)),
        description="URL to card benefits page"
    )
    is_available_in_market: bool = Field(
        default=True,
        description="If False, card is discontinued or not available for new applications"
    )
    yaml_filename: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), unique=True, index=True),
        description="Name of the YAML file that defines this card (e.g., 'icici_international.yaml'). Used as unique identifier for card import/update/delete operations."
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCard(SQLModel, table=True):
    """
    User's actual credit card instance.
    Links Plaid account to a CardProduct for reward calculation.
    
    Sprint 1: Separated from CardProduct. Each user has their own UserCard instances
    that optionally link to CardProducts in the shared library.
    """
    __tablename__ = "user_cards"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    card_product_id: Optional[UUID] = Field(
        default=None,
        foreign_key="card_products.id",
        description="Identified card product (NULL until user identifies this card)"
    )
    
    # Plaid linkage
    plaid_item_id: UUID = Field(foreign_key="plaid_items.id", nullable=False, index=True)
    plaid_account_id: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False, index=True),
        description="Plaid's account ID - unique per credit card account"
    )
    official_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500)),
        description="Official name from Plaid (e.g., 'Chase Credit Card')"
    )
    mask: Optional[str] = Field(
        default=None,
        sa_column=Column(String(10)),
        description="Last 4 digits of card (e.g., '1234')"
    )
    
    # Status
    is_active: bool = Field(
        default=True,
        description="False if card is closed or inactive"
    )
    identified_at: Optional[datetime] = Field(
        default=None,
        description="When user identified this card as a specific CardProduct"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RewardRule(SQLModel, table=True):
    """
    Reward multipliers for specific spending categories per card product.
    
    Sprint 1: Now links to CardProduct instead of individual user cards.
    Each CardProduct can have multiple reward rules, one per bucket.
    
    Example:
    - Chase Freedom Unlimited (CardProduct): 3x on DINING, 3x on DRUGSTORE, 1.5x on GENERAL
    - Amex Gold (CardProduct): 4x on DINING, 4x on GROCERY, 3x on TRAVEL
    """
    __tablename__ = "reward_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    card_product_id: UUID = Field(
        foreign_key="card_products.id",
        nullable=False,
        index=True,
        description="Links to CardProduct in the master library"
    )
    
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
    
    Sprint 1: Now references UserCard instead of Card.
    
    Key Fields:
    - plaid_transaction_id: Unique identifier from Plaid (natural key for idempotent upserts)
    - is_analyzable: False for refunds, payments, transfers (filtered per SRS Section 2.2)
    - amount: Stored as Decimal(12,2) for precise financial calculations
    """
    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_card_id: UUID = Field(
        foreign_key="user_cards.id",
        nullable=False,
        index=True,
        description="Which UserCard was used for this transaction"
    )
    
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
    
    # Optimization results (to be populated by optimization engine)
    actual_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Cashback earned on the card used"
    )
    best_user_card_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user_cards.id",
        description="Best UserCard from user's identified cards"
    )
    best_possible_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Maximum possible cashback from best identified user card"
    )
    lost_savings: Decimal = Field(
        default=Decimal("0.0"),
        sa_column=Column(DECIMAL(10, 2), nullable=False),
        description="Opportunity cost from identified cards (best_possible - actual)"
    )
    
    # Market analysis - Best card product from entire library
    market_winner_product_id: Optional[UUID] = Field(
        default=None,
        foreign_key="card_products.id",
        description="Best CardProduct from entire market library"
    )
    market_winner_cashback: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(DECIMAL(10, 2)),
        description="Maximum possible cashback from market winner CardProduct"
    )
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Force Pydantic to resolve all forward references after all classes are defined
# This prevents RecursionError in Pydantic v2's _repr logic
User.model_rebuild()
PlaidItem.model_rebuild()
CardProduct.model_rebuild()
UserCard.model_rebuild()
RewardRule.model_rebuild()
Transaction.model_rebuild()

