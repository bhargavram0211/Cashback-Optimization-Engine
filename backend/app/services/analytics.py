"""
Cashback Optimization Engine - Analytics Service
Sprint 1: Updated to work with UserCard and CardProduct architecture
Provides aggregate insights and recommendations using efficient SQL queries
"""

from sqlmodel import Session, select, func
from app.models import Transaction, UserCard, CardProduct, PlaidItem
from typing import Dict, List, Any, Optional
from decimal import Decimal
from uuid import UUID


class AnalyticsService:
    """
    Service for calculating analytics metrics using database-side aggregations.
    All methods use SQLAlchemy func.sum, func.count, and GROUP BY for efficiency.
    """

    @staticmethod
    def get_savings_summary(session: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Calculate aggregate spending and opportunity cost metrics for a user.
        
        Sprint 1: Updated to use UserCard instead of Card.
        
        Args:
            session: Database session
            user_id: UUID of the user
            
        Returns:
            Dictionary with total_spent, total_lost_savings, total_earned, transaction_count
        """
        # Build query with JOINs to filter by user_id
        query = (
            select(
                func.sum(Transaction.amount).label("total_spent"),
                func.sum(Transaction.lost_savings).label("total_lost_savings"),
                func.sum(Transaction.actual_cashback).label("total_earned"),
                func.count(Transaction.id).label("transaction_count")
            )
            .join(UserCard, Transaction.user_card_id == UserCard.id)
            .join(PlaidItem, UserCard.plaid_item_id == PlaidItem.id)
            .where(PlaidItem.user_id == UUID(user_id))
            .where(Transaction.is_analyzable == True)
        )
        
        result = session.exec(query).first()
        
        if not result or result[0] is None:
            return None
            
        return {
            "total_spent": float(result[0]) if result[0] else 0.0,
            "total_lost_savings": float(result[1]) if result[1] else 0.0,
            "total_earned": float(result[2]) if result[2] else 0.0,
            "transaction_count": result[3] if result[3] else 0,
            "total_potential": float(result[2] + result[1]) if result[2] and result[1] else 0.0
        }

    @staticmethod
    def get_category_breakdown(session: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Group transactions by internal_bucket and calculate opportunity cost per category.
        
        Sprint 1: Updated to use UserCard instead of Card.
        
        Args:
            session: Database session
            user_id: UUID of the user
            
        Returns:
            List of dictionaries with bucket, transaction_count, total_spent, lost_savings
        """
        # Define aggregations with labels
        lost_savings_sum = func.sum(Transaction.lost_savings).label("lost_savings")
        
        query = (
            select(
                Transaction.internal_bucket,
                func.count(Transaction.id).label("transaction_count"),
                func.sum(Transaction.amount).label("total_spent"),
                lost_savings_sum,
                func.sum(Transaction.actual_cashback).label("actual_cashback"),
                func.sum(Transaction.best_possible_cashback).label("potential_cashback")
            )
            .join(UserCard, Transaction.user_card_id == UserCard.id)
            .join(PlaidItem, UserCard.plaid_item_id == PlaidItem.id)
            .where(PlaidItem.user_id == UUID(user_id))
            .where(Transaction.is_analyzable == True)
            .group_by(Transaction.internal_bucket)
            .order_by(lost_savings_sum.desc())
        )
        
        results = session.exec(query).all()
        
        breakdown = []
        for row in results:
            breakdown.append({
                "category": row[0],
                "transaction_count": row[1],
                "total_spent": float(row[2]) if row[2] else 0.0,
                "lost_savings": float(row[3]) if row[3] else 0.0,
                "actual_cashback": float(row[4]) if row[4] else 0.0,
                "potential_cashback": float(row[5]) if row[5] else 0.0
            })
        
        return breakdown

    @staticmethod
    def get_top_recommendation(session: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Identify the card that would save the most money if the user switched to it.
        
        Sprint 1: Now joins through UserCard → CardProduct to get card details.
        
        Args:
            session: Database session
            user_id: UUID of the user
            
        Returns:
            Dictionary with card details, times_recommended, and total_potential_savings
        """
        # Define aggregation with label for ORDER BY
        total_potential_savings = func.sum(Transaction.lost_savings).label("total_potential_savings")
        
        # Use aliased UserCard to join through best_user_card_id
        # Filter by user_id through the transaction's user_card_id (the card that was actually used)
        from sqlalchemy.orm import aliased
        BestUserCard = aliased(UserCard)
        UsedUserCard = aliased(UserCard)
        
        query = (
            select(
                CardProduct.provider,
                CardProduct.card_name,
                func.count(Transaction.id).label("times_recommended"),
                total_potential_savings,
                func.avg(Transaction.lost_savings).label("avg_savings_per_transaction")
            )
            .join(UsedUserCard, Transaction.user_card_id == UsedUserCard.id)
            .join(PlaidItem, UsedUserCard.plaid_item_id == PlaidItem.id)
            .join(BestUserCard, Transaction.best_user_card_id == BestUserCard.id)
            .join(CardProduct, BestUserCard.card_product_id == CardProduct.id)
            .where(PlaidItem.user_id == UUID(user_id))
            .where(Transaction.is_analyzable == True)
            .where(Transaction.best_user_card_id.isnot(None))
            .group_by(CardProduct.id, CardProduct.provider, CardProduct.card_name)
            .order_by(total_potential_savings.desc())
            .limit(1)
        )
        
        result = session.exec(query).first()
        
        if not result:
            return None
            
        return {
            "provider": result[0],
            "card_name": result[1],
            "times_recommended": result[2],
            "total_potential_savings": float(result[3]) if result[3] else 0.0,
            "avg_savings_per_transaction": float(result[4]) if result[4] else 0.0
        }

    @staticmethod
    def get_card_performance_comparison(session: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Compare all cards and show how much each could save if used optimally.
        
        Sprint 1: Now joins through UserCard → CardProduct.
        
        Args:
            session: Database session
            user_id: UUID of the user
            
        Returns:
            List of dictionaries with card details and potential savings
        """
        # Define aggregation with label for ORDER BY
        potential_savings = func.sum(Transaction.lost_savings).label("potential_savings")
        
        # Use aliased UserCard to join through best_user_card_id
        # Filter by user_id through the transaction's user_card_id (the card that was actually used)
        from sqlalchemy.orm import aliased
        BestUserCard = aliased(UserCard)
        UsedUserCard = aliased(UserCard)
        
        query = (
            select(
                CardProduct.provider,
                CardProduct.card_name,
                func.count(Transaction.id).label("optimal_transaction_count"),
                potential_savings
            )
            .join(UsedUserCard, Transaction.user_card_id == UsedUserCard.id)
            .join(PlaidItem, UsedUserCard.plaid_item_id == PlaidItem.id)
            .join(BestUserCard, Transaction.best_user_card_id == BestUserCard.id)
            .join(CardProduct, BestUserCard.card_product_id == CardProduct.id)
            .where(PlaidItem.user_id == UUID(user_id))
            .where(Transaction.is_analyzable == True)
            .where(Transaction.best_user_card_id.isnot(None))
            .group_by(CardProduct.id, CardProduct.provider, CardProduct.card_name)
            .order_by(potential_savings.desc())
        )
        
        results = session.exec(query).all()
        
        comparison = []
        for row in results:
            comparison.append({
                "provider": row[0],
                "card_name": row[1],
                "optimal_transaction_count": row[2],
                "potential_savings": float(row[3]) if row[3] else 0.0
            })
        
        return comparison

    @staticmethod
    def get_optimization_opportunities(session: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Get individual transactions with optimization opportunities (lost_savings > 0).
        
        Returns transaction details including merchant, category, amounts, and 
        the recommended optimal card for each transaction.
        
        Sprint 1: Now joins through UserCard → CardProduct for card details.
        
        Args:
            session: Database session
            user_id: UUID of the user
            
        Returns:
            List of dictionaries with transaction details and recommendations
        """
        # Join pattern: Transaction -> best_user_card (UserCard) -> CardProduct
        # AND Transaction -> used_user_card (UserCard) -> PlaidItem (for user filter)
        # We need to alias the UserCards and CardProducts to differentiate
        from sqlalchemy.orm import aliased
        
        BestUserCard = aliased(UserCard)
        UsedUserCard = aliased(UserCard)
        BestCardProduct = aliased(CardProduct)
        UsedCardProduct = aliased(CardProduct)
        
        query = (
            select(
                Transaction.merchant_name,
                Transaction.amount,
                Transaction.date,
                Transaction.internal_bucket,
                Transaction.actual_cashback,
                Transaction.best_possible_cashback,
                Transaction.lost_savings,
                BestCardProduct.provider,
                BestCardProduct.card_name,
                UsedCardProduct.provider,
                UsedCardProduct.card_name
            )
            .join(UsedUserCard, Transaction.user_card_id == UsedUserCard.id)
            .join(PlaidItem, UsedUserCard.plaid_item_id == PlaidItem.id)
            .join(UsedCardProduct, UsedUserCard.card_product_id == UsedCardProduct.id)
            .join(BestUserCard, Transaction.best_user_card_id == BestUserCard.id)
            .join(BestCardProduct, BestUserCard.card_product_id == BestCardProduct.id)
            .where(PlaidItem.user_id == UUID(user_id))
            .where(Transaction.is_analyzable == True)
            .where(Transaction.lost_savings > 0)
            .order_by(Transaction.lost_savings.desc())
            .limit(50)  # Limit to top 50 opportunities for performance
        )
        
        results = session.exec(query).all()
        
        opportunities = []
        for row in results:
            opportunities.append({
                "merchant_name": row[0],
                "amount": float(row[1]) if row[1] else 0.0,
                "date": str(row[2]) if row[2] else None,
                "internal_bucket": row[3],
                "actual_cashback": float(row[4]) if row[4] else 0.0,
                "best_possible_cashback": float(row[5]) if row[5] else 0.0,
                "lost_savings": float(row[6]) if row[6] else 0.0,
                "best_card_provider": row[7],
                "best_card_name": row[8],
                "used_card_provider": row[9],
                "used_card_name": row[10]
            })
        
        return opportunities

