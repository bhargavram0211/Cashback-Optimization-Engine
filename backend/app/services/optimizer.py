"""
Sprint 1: Cashback Optimization Engine (Refactored)
Calculates optimal card usage and opportunity cost for each transaction.

Sprint 1 Changes:
- Works with UserCard (user instances) and CardProduct (master library)
- Only calculates rewards for identified cards (where card_product_id is set)
- Scans user's identified cards for "best_user_card"
- Scans entire CardProduct library for "market_winner"
"""

from decimal import Decimal
from typing import Dict, Tuple, Optional
from uuid import UUID

from sqlmodel import Session, select
from app.models import UserCard, CardProduct, RewardRule, Transaction


def get_user_card_multiplier(
    session: Session,
    user_card_id: UUID,
    bucket: str
) -> Decimal:
    """
    Get the reward multiplier for a user's card and bucket.
    
    Sprint 1: Now looks up UserCard → CardProduct → RewardRule
    
    Logic:
    1. Get UserCard
    2. Check if identified (has card_product_id)
    3. Get CardProduct
    4. Check for specific RewardRule, else use base rate
    
    Args:
        session: Database session
        user_card_id: UUID of the UserCard
        bucket: Internal reward bucket (DINING, GROCERY, etc.)
    
    Returns:
        Decimal multiplier (e.g., 3.0 for 3x, 1.5 for 1.5x)
    """
    # Get UserCard
    user_card = session.exec(
        select(UserCard).where(UserCard.id == user_card_id)
    ).first()
    
    if not user_card or not user_card.card_product_id:
        # Unidentified card, default to 1%
        return Decimal("1.0")
    
    # Get CardProduct
    card_product = session.exec(
        select(CardProduct).where(CardProduct.id == user_card.card_product_id)
    ).first()
    
    if not card_product:
        return Decimal("1.0")
    
    # Check for specific reward rule
    rule = session.exec(
        select(RewardRule).where(
            RewardRule.card_product_id == card_product.id,
            RewardRule.bucket == bucket
        )
    ).first()
    
    if rule:
        return rule.multiplier
    
    return card_product.base_reward_rate


def get_card_product_multiplier(
    session: Session,
    card_product_id: UUID,
    bucket: str
) -> Decimal:
    """
    Get the reward multiplier for a CardProduct and bucket.
    
    Sprint 1: Used for market analysis (scanning all CardProducts).
    
    Args:
        session: Database session
        card_product_id: UUID of the CardProduct
        bucket: Internal reward bucket
    
    Returns:
        Decimal multiplier
    """
    # Get CardProduct
    card_product = session.exec(
        select(CardProduct).where(CardProduct.id == card_product_id)
    ).first()
    
    if not card_product:
        return Decimal("1.0")
    
    # Check for specific reward rule
    rule = session.exec(
        select(RewardRule).where(
            RewardRule.card_product_id == card_product.id,
            RewardRule.bucket == bucket
        )
    ).first()
    
    if rule:
        return rule.multiplier
    
    return card_product.base_reward_rate


def find_best_user_card_for_bucket(
    session: Session,
    user_id: UUID,
    bucket: str,
    exclude_user_card_id: Optional[UUID] = None
) -> Tuple[Optional[UUID], Decimal]:
    """
    Find the best UserCard from user's identified cards for a given bucket.
    
    Sprint 1: Scans only the user's identified UserCards.
    Only considers cards where card_product_id is set.
    
    Args:
        session: Database session
        user_id: UUID of the user
        bucket: Internal reward bucket
        exclude_user_card_id: Optional UserCard to exclude from search
    
    Returns:
        Tuple of (best_user_card_id, best_multiplier)
    """
    # Get user's identified cards
    user_cards_statement = select(UserCard).where(
        UserCard.user_id == user_id,
        UserCard.card_product_id != None,  # Only identified cards
        UserCard.is_active == True
    )
    user_cards = session.exec(user_cards_statement).all()
    
    best_user_card_id = None
    best_multiplier = Decimal("0.0")
    
    for user_card in user_cards:
        if exclude_user_card_id and user_card.id == exclude_user_card_id:
            continue
        
        multiplier = get_user_card_multiplier(session, user_card.id, bucket)
        
        if multiplier > best_multiplier:
            best_multiplier = multiplier
            best_user_card_id = user_card.id
    
    return best_user_card_id, best_multiplier


def find_best_card_product_for_bucket(
    session: Session,
    bucket: str
) -> Tuple[Optional[UUID], Decimal]:
    """
    Find the best CardProduct from entire library for a given bucket.
    
    Sprint 1: Market analysis - scans all available CardProducts.
    
    Args:
        session: Database session
        bucket: Internal reward bucket
    
    Returns:
        Tuple of (best_card_product_id, best_multiplier)
    """
    # Get all available card products
    products_statement = select(CardProduct).where(
        CardProduct.is_available_in_market == True
    )
    products = session.exec(products_statement).all()
    
    best_product_id = None
    best_multiplier = Decimal("0.0")
    
    for product in products:
        multiplier = get_card_product_multiplier(session, product.id, bucket)
        
        if multiplier > best_multiplier:
            best_multiplier = multiplier
            best_product_id = product.id
    
    return best_product_id, best_multiplier


def calculate_cashback(amount: Decimal, multiplier: Decimal) -> Decimal:
    """
    Calculate cashback amount.
    
    Formula: amount * (multiplier / 100)
    
    Example:
        $100 purchase with 3x multiplier = $100 * (3.0 / 100) = $3.00
    
    Args:
        amount: Transaction amount
        multiplier: Reward multiplier (e.g., 3.0 for 3x)
    
    Returns:
        Cashback amount in dollars
    """
    return amount * (multiplier / Decimal("100"))


def optimize_transaction(session: Session, transaction: Transaction) -> Dict[str, any]:
    """
    Optimize a single transaction.
    
    Sprint 1: Now works with UserCard and CardProduct architecture.
    
    Calculates:
    - actual_cashback: What was earned with the UserCard used
    - best_user_card_id: Which identified UserCard would have been optimal
    - best_possible_cashback: What could have been earned with best identified card
    - lost_savings: Opportunity cost (from identified cards)
    - market_winner_product_id: Which CardProduct from library is best
    - market_winner_cashback: What could be earned if user had that card
    
    Args:
        session: Database session
        transaction: Transaction to optimize
    
    Returns:
        Dict with optimization results
    """
    # Skip non-analyzable transactions
    if not transaction.is_analyzable:
        return {
            "optimized": False,
            "reason": "non_analyzable"
        }
    
    # Skip if no bucket assigned
    if not transaction.internal_bucket:
        return {
            "optimized": False,
            "reason": "no_bucket"
        }
    
    # Get the UserCard that was used
    user_card = session.exec(
        select(UserCard).where(UserCard.id == transaction.user_card_id)
    ).first()
    
    if not user_card:
        return {
            "optimized": False,
            "reason": "user_card_not_found"
        }
    
    # Get current UserCard's multiplier
    current_multiplier = get_user_card_multiplier(
        session,
        transaction.user_card_id,
        transaction.internal_bucket
    )
    
    # Calculate what was actually earned
    actual_cashback = calculate_cashback(transaction.amount, current_multiplier)
    
    # PASS 1: Find the best IDENTIFIED UserCard for lost_savings calculation
    # This only considers the user's identified cards
    best_user_card_id, best_multiplier = find_best_user_card_for_bucket(
        session,
        user_card.user_id,
        transaction.internal_bucket
    )
    
    # Calculate what could have been earned with best identified card
    best_possible_cashback = calculate_cashback(transaction.amount, best_multiplier)
    
    # Calculate opportunity cost (from identified cards)
    lost_savings = best_possible_cashback - actual_cashback
    
    # PASS 2: Find the MARKET WINNER from entire CardProduct library
    # This scans all available CardProducts for market comparison
    market_winner_product_id, market_winner_multiplier = find_best_card_product_for_bucket(
        session,
        transaction.internal_bucket
    )
    
    # Calculate what could have been earned with the absolute best market card
    market_winner_cashback = calculate_cashback(transaction.amount, market_winner_multiplier)
    
    # Update transaction with BOTH user wallet and market results
    transaction.actual_cashback = actual_cashback
    transaction.best_user_card_id = best_user_card_id
    transaction.best_possible_cashback = best_possible_cashback
    transaction.lost_savings = lost_savings
    transaction.market_winner_product_id = market_winner_product_id
    transaction.market_winner_cashback = market_winner_cashback
    
    return {
        "optimized": True,
        "actual_cashback": float(actual_cashback),
        "best_possible_cashback": float(best_possible_cashback),
        "lost_savings": float(lost_savings),
        "market_winner_cashback": float(market_winner_cashback)
    }


def optimize_all_transactions(session: Session) -> Dict[str, any]:
    """
    Optimize all transactions in the database.
    
    Main entry point for the optimization engine.
    
    Process:
    1. Fetch all transactions
    2. For each transaction, calculate optimal card usage
    3. Update transaction with optimization results
    4. Return summary statistics
    
    Returns:
        Dict with optimization summary
    """
    print("🔍 Starting optimization engine...")
    
    # Get all transactions
    statement = select(Transaction)
    transactions = session.exec(statement).all()
    
    if not transactions:
        return {
            "status": "no_transactions",
            "message": "No transactions found in database"
        }
    
    print(f"📊 Found {len(transactions)} transactions to optimize")
    
    # Statistics
    stats = {
        "total_transactions": len(transactions),
        "optimized": 0,
        "skipped_non_analyzable": 0,
        "skipped_no_bucket": 0,
        "total_actual_cashback": Decimal("0.0"),
        "total_potential_cashback": Decimal("0.0"),
        "total_lost_savings": Decimal("0.0")
    }
    
    # Optimize each transaction
    for txn in transactions:
        result = optimize_transaction(session, txn)
        
        if result["optimized"]:
            stats["optimized"] += 1
            stats["total_actual_cashback"] += txn.actual_cashback or Decimal("0.0")
            stats["total_potential_cashback"] += txn.best_possible_cashback or Decimal("0.0")
            stats["total_lost_savings"] += txn.lost_savings or Decimal("0.0")
        elif result["reason"] == "non_analyzable":
            stats["skipped_non_analyzable"] += 1
        elif result["reason"] == "no_bucket":
            stats["skipped_no_bucket"] += 1
    
    # Commit all changes
    session.commit()
    
    print(f"✅ Optimized {stats['optimized']} transactions")
    print(f"⏭️  Skipped {stats['skipped_non_analyzable']} non-analyzable transactions")
    print(f"⏭️  Skipped {stats['skipped_no_bucket']} transactions without bucket")
    print(f"💰 Total opportunity cost: ${stats['total_lost_savings']:.2f}")
    
    return {
        "status": "success",
        "total_transactions": stats["total_transactions"],
        "optimized": stats["optimized"],
        "skipped": stats["skipped_non_analyzable"] + stats["skipped_no_bucket"],
        "total_actual_cashback": float(stats["total_actual_cashback"]),
        "total_potential_cashback": float(stats["total_potential_cashback"]),
        "total_lost_savings": float(stats["total_lost_savings"]),
        "average_lost_per_transaction": float(
            stats["total_lost_savings"] / stats["optimized"]
            if stats["optimized"] > 0 else 0
        )
    }

