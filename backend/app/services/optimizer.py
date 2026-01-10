"""
Phase 2.2: Cashback Optimization Engine
Calculates optimal card usage and opportunity cost for each transaction.

Core Logic:
- For each transaction, determine which card would have yielded the highest cashback
- Calculate actual_cashback (what was earned with the card used)
- Calculate best_possible_cashback (what could have been earned with optimal card)
- Calculate lost_savings (opportunity cost)
"""

from decimal import Decimal
from typing import Dict, Tuple, Optional
from uuid import UUID

from sqlmodel import Session, select
from app.models import Card, RewardRule, Transaction


def get_card_multiplier(
    session: Session, 
    card_id: UUID, 
    bucket: str
) -> Decimal:
    """
    Get the reward multiplier for a specific card and bucket.
    
    Logic:
    1. Check if card has a specific rule for this bucket
    2. If not, use the card's base_reward_rate
    
    Args:
        session: Database session
        card_id: UUID of the card
        bucket: Internal reward bucket (DINING, GROCERY, etc.)
    
    Returns:
        Decimal multiplier (e.g., 3.0 for 3x, 1.5 for 1.5x)
    """
    # Try to find a specific rule for this bucket
    rule_statement = select(RewardRule).where(
        RewardRule.card_id == card_id,
        RewardRule.bucket == bucket
    )
    rule = session.exec(rule_statement).first()
    
    if rule:
        return rule.multiplier
    
    # No specific rule, use card's base rate
    card_statement = select(Card).where(Card.id == card_id)
    card = session.exec(card_statement).first()
    
    if card:
        return card.base_reward_rate
    
    # Fallback (shouldn't happen if DB integrity is maintained)
    return Decimal("1.0")


def find_best_card_for_bucket(
    session: Session,
    bucket: str,
    exclude_card_id: Optional[UUID] = None
) -> Tuple[UUID, Decimal]:
    """
    Find the card with the highest multiplier for a given bucket.
    
    Args:
        session: Database session
        bucket: Internal reward bucket
        exclude_card_id: Optional card to exclude from search
    
    Returns:
        Tuple of (best_card_id, best_multiplier)
    """
    # Get all cards
    cards_statement = select(Card)
    cards = session.exec(cards_statement).all()
    
    best_card_id = None
    best_multiplier = Decimal("0.0")
    
    for card in cards:
        if exclude_card_id and card.id == exclude_card_id:
            continue
        
        multiplier = get_card_multiplier(session, card.id, bucket)
        
        if multiplier > best_multiplier:
            best_multiplier = multiplier
            best_card_id = card.id
    
    return best_card_id, best_multiplier


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
    
    Calculates:
    - actual_cashback: What was earned with the card used
    - best_card_id: Which card would have been optimal
    - best_possible_cashback: What could have been earned
    - lost_savings: Opportunity cost
    
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
    
    # Get current card's multiplier
    current_multiplier = get_card_multiplier(
        session, 
        transaction.card_id, 
        transaction.internal_bucket
    )
    
    # Calculate what was actually earned
    actual_cashback = calculate_cashback(transaction.amount, current_multiplier)
    
    # Find the best card for this bucket
    best_card_id, best_multiplier = find_best_card_for_bucket(
        session,
        transaction.internal_bucket
    )
    
    # Calculate what could have been earned
    best_possible_cashback = calculate_cashback(transaction.amount, best_multiplier)
    
    # Calculate opportunity cost
    lost_savings = best_possible_cashback - actual_cashback
    
    # Update transaction
    transaction.actual_cashback = actual_cashback
    transaction.best_card_id = best_card_id
    transaction.best_possible_cashback = best_possible_cashback
    transaction.lost_savings = lost_savings
    
    return {
        "optimized": True,
        "actual_cashback": float(actual_cashback),
        "best_possible_cashback": float(best_possible_cashback),
        "lost_savings": float(lost_savings)
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

