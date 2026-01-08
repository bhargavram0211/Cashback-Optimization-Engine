#!/usr/bin/env python3
"""
Phase 2.2: POC Card Seeding Script
Seeds 4 real-world credit cards with their reward structures.

This script:
1. Creates 4 cards (Chase, Discover, BofA, Zolve)
2. Inserts reward rules for each card
3. Updates all transactions to use Zolve US (suboptimal card)

Usage:
    python scripts/seed_poc_cards.py
"""

import sys
import os
from decimal import Decimal
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models import Card, RewardRule, Transaction


# Card definitions with their reward structures
CARDS_DATA = [
    {
        "provider": "Chase",
        "card_name": "Freedom Unlimited",
        "base_reward_rate": Decimal("1.5"),
        "rules": [
            {"bucket": "DINING", "multiplier": Decimal("3.0")},
            {"bucket": "DRUGSTORE", "multiplier": Decimal("3.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.5")},
        ]
    },
    {
        "provider": "Discover",
        "card_name": "it",
        "base_reward_rate": Decimal("1.0"),
        "rules": [
            {"bucket": "GROCERY", "multiplier": Decimal("5.0")},
            {"bucket": "WHOLESALE", "multiplier": Decimal("5.0")},
            {"bucket": "STREAMING", "multiplier": Decimal("5.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    {
        "provider": "Bank of America",
        "card_name": "Customized Cash",
        "base_reward_rate": Decimal("1.0"),
        "rules": [
            {"bucket": "ONLINE_SHOPPING", "multiplier": Decimal("3.0")},
            {"bucket": "GROCERY", "multiplier": Decimal("2.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    {
        "provider": "Zolve",
        "card_name": "US",
        "base_reward_rate": Decimal("1.0"),
        "rules": [
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    }
]


def get_or_create_plaid_item(session: Session) -> UUID:
    """
    Get the first PlaidItem ID, or create a dummy one if none exist.
    Cards need to be linked to a PlaidItem.
    """
    from app.models import PlaidItem, User
    
    # Try to get first plaid item
    statement = select(PlaidItem).limit(1)
    plaid_item = session.exec(statement).first()
    
    if plaid_item:
        print(f"✓ Using existing PlaidItem: {plaid_item.id}")
        return plaid_item.id
    
    # Need to create a dummy user and plaid item
    print("⚠️  No PlaidItem found. Creating dummy user and PlaidItem for seeding...")
    
    # Create dummy user
    user_statement = select(User).limit(1)
    user = session.exec(user_statement).first()
    
    if not user:
        user = User(email="seed_user@cashback.local")
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"✓ Created dummy user: {user.email}")
    
    # Create dummy plaid item
    plaid_item = PlaidItem(
        user_id=user.id,
        access_token="seed_dummy_token",
        institution_name="Seed Institution"
    )
    session.add(plaid_item)
    session.commit()
    session.refresh(plaid_item)
    print(f"✓ Created dummy PlaidItem: {plaid_item.id}")
    
    return plaid_item.id


def seed_cards(session: Session):
    """
    Insert the 4 POC cards with their reward rules.
    Returns the ID of the Zolve US card.
    """
    print("\n" + "="*70)
    print("PHASE 2.2: SEEDING POC CARDS")
    print("="*70 + "\n")
    
    # Get or create a PlaidItem to link cards to
    plaid_item_id = get_or_create_plaid_item(session)
    
    zolve_card_id = None
    
    for idx, card_data in enumerate(CARDS_DATA, start=1):
        # Check if card already exists (by provider + card_name)
        statement = select(Card).where(
            Card.provider == card_data["provider"],
            Card.card_name == card_data["card_name"]
        )
        existing_card = session.exec(statement).first()
        
        if existing_card:
            print(f"\n{idx}. {card_data['provider']} {card_data['card_name']}")
            print(f"   ⚠️  Card already exists (ID: {existing_card.id})")
            card = existing_card
        else:
            # Create new card
            card = Card(
                plaid_item_id=plaid_item_id,
                plaid_account_id=f"seed_account_{card_data['provider'].lower().replace(' ', '_')}_{card_data['card_name'].lower().replace(' ', '_')}",
                official_name=f"{card_data['provider']} {card_data['card_name']}",
                provider=card_data["provider"],
                card_name=card_data["card_name"],
                base_reward_rate=card_data["base_reward_rate"],
                mask="SEED"
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            
            print(f"\n{idx}. {card_data['provider']} {card_data['card_name']}")
            print(f"   ✓ Card created (ID: {card.id})")
            print(f"   Base rate: {card.base_reward_rate}%")
        
        # Remember Zolve card ID
        if card_data["provider"] == "Zolve":
            zolve_card_id = card.id
        
        # Insert reward rules
        for rule_data in card_data["rules"]:
            # Check if rule exists
            rule_statement = select(RewardRule).where(
                RewardRule.card_id == card.id,
                RewardRule.bucket == rule_data["bucket"]
            )
            existing_rule = session.exec(rule_statement).first()
            
            if existing_rule:
                # Update existing rule
                existing_rule.multiplier = rule_data["multiplier"]
                session.commit()
                print(f"   ↻ Updated rule: {rule_data['bucket']} → {rule_data['multiplier']}x")
            else:
                # Create new rule
                rule = RewardRule(
                    card_id=card.id,
                    bucket=rule_data["bucket"],
                    multiplier=rule_data["multiplier"]
                )
                session.add(rule)
                session.commit()
                print(f"   ✓ Rule added: {rule_data['bucket']} → {rule_data['multiplier']}x")
    
    return zolve_card_id


def manipulate_transactions(session: Session, zolve_card_id: UUID):
    """
    The Manipulation: Set all transactions to use the Zolve US card.
    This simulates suboptimal card usage to demonstrate the optimizer.
    """
    print("\n" + "="*70)
    print("THE MANIPULATION: Setting all transactions to Zolve US")
    print("="*70 + "\n")
    
    # Get all transactions
    statement = select(Transaction)
    transactions = session.exec(statement).all()
    
    if not transactions:
        print("⚠️  No transactions found in database. Run sync first!")
        return
    
    print(f"Found {len(transactions)} transactions")
    print(f"Setting card_id to Zolve US: {zolve_card_id}")
    
    updated_count = 0
    for txn in transactions:
        if txn.card_id != zolve_card_id:
            txn.card_id = zolve_card_id
            updated_count += 1
    
    session.commit()
    
    print(f"✓ Updated {updated_count} transactions to use Zolve US")
    print(f"  (This simulates always using the suboptimal 1% flat card)")


def main():
    """Main seeding process"""
    with Session(engine) as session:
        try:
            # Step 1: Seed cards and rules
            zolve_card_id = seed_cards(session)
            
            if not zolve_card_id:
                print("\n❌ ERROR: Failed to create or find Zolve US card")
                return 1
            
            # Step 2: Manipulate transactions
            manipulate_transactions(session, zolve_card_id)
            
            # Summary
            print("\n" + "="*70)
            print("SEEDING COMPLETE!")
            print("="*70)
            
            # Count cards and rules
            cards_statement = select(Card).where(Card.mask == "SEED")
            cards_count = len(session.exec(cards_statement).all())
            
            rules_statement = select(RewardRule)
            rules_count = len(session.exec(rules_statement).all())
            
            txn_statement = select(Transaction).where(Transaction.card_id == zolve_card_id)
            txn_count = len(session.exec(txn_statement).all())
            
            print(f"\n✅ {cards_count} POC cards created")
            print(f"✅ {rules_count} reward rules configured")
            print(f"✅ {txn_count} transactions set to Zolve US (suboptimal)")
            print(f"\n🎯 Ready to run optimizer: POST /optimize")
            print(f"   Expected: Discover significant opportunity cost!\n")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    exit(main())

