#!/usr/bin/env python3
"""
Phase 3.2: Market Library Card Seeding Script
Seeds 10 total credit cards: 4 wallet cards + 6 market cards.

This script:
1. Creates 4 wallet cards (is_in_user_wallet=True): Chase, Discover, BofA, Zolve
2. Creates 6 market cards (is_in_user_wallet=False): Amex Gold, Cap One Savor, etc.
3. Inserts reward rules for each card
4. Updates all transactions to use Zolve US (suboptimal card)

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
# Phase 3.2: 4 wallet cards + 6 market cards = 10 total
CARDS_DATA = [
    # ========== WALLET CARDS (is_in_user_wallet=True) ==========
    {
        "provider": "Chase",
        "card_name": "Freedom Unlimited",
        "base_reward_rate": Decimal("1.5"),
        "is_in_user_wallet": True,
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
        "is_in_user_wallet": True,
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
        "is_in_user_wallet": True,
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
        "is_in_user_wallet": True,
        "rules": [
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    
    # ========== MARKET CARDS (is_in_user_wallet=False) ==========
    {
        "provider": "American Express",
        "card_name": "Gold Card",
        "base_reward_rate": Decimal("1.0"),
        "is_in_user_wallet": False,
        "rules": [
            {"bucket": "DINING", "multiplier": Decimal("4.0")},
            {"bucket": "GROCERY", "multiplier": Decimal("4.0")},
            {"bucket": "TRAVEL", "multiplier": Decimal("3.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    {
        "provider": "Capital One",
        "card_name": "SavorOne",
        "base_reward_rate": Decimal("1.0"),
        "is_in_user_wallet": False,
        "rules": [
            {"bucket": "DINING", "multiplier": Decimal("4.0")},
            {"bucket": "STREAMING", "multiplier": Decimal("4.0")},
            {"bucket": "GROCERY", "multiplier": Decimal("3.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    {
        "provider": "American Express",
        "card_name": "Blue Cash Everyday",
        "base_reward_rate": Decimal("1.0"),
        "is_in_user_wallet": False,
        "rules": [
            {"bucket": "ONLINE_SHOPPING", "multiplier": Decimal("3.0")},
            {"bucket": "GAS", "multiplier": Decimal("3.0")},
            {"bucket": "GROCERY", "multiplier": Decimal("3.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    {
        "provider": "Citi",
        "card_name": "Custom Cash",
        "base_reward_rate": Decimal("1.0"),
        "is_in_user_wallet": False,
        "rules": [
            # Note: Citi Custom Cash gives 5% on top spend category up to $500/month
            # For simplicity, applying 5% to major categories
            {"bucket": "DINING", "multiplier": Decimal("5.0")},
            {"bucket": "GROCERY", "multiplier": Decimal("5.0")},
            {"bucket": "GAS", "multiplier": Decimal("5.0")},
            {"bucket": "TRAVEL", "multiplier": Decimal("5.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
    {
        "provider": "Capital One",
        "card_name": "Venture X",
        "base_reward_rate": Decimal("2.0"),
        "is_in_user_wallet": False,
        "rules": [
            {"bucket": "GENERAL", "multiplier": Decimal("2.0")},
        ]
    },
    {
        "provider": "American Express",
        "card_name": "Platinum Card",
        "base_reward_rate": Decimal("1.0"),
        "is_in_user_wallet": False,
        "rules": [
            {"bucket": "TRAVEL", "multiplier": Decimal("5.0")},
            {"bucket": "GENERAL", "multiplier": Decimal("1.0")},
        ]
    },
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
    Insert the 10 cards (4 wallet + 6 market) with their reward rules.
    Returns the ID of the Zolve US card.
    """
    print("\n" + "="*70)
    print("PHASE 3.2: SEEDING MARKET LIBRARY (10 CARDS)")
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
                is_in_user_wallet=card_data.get("is_in_user_wallet", False),
                mask="SEED"
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            
            wallet_status = "🔵 WALLET" if card.is_in_user_wallet else "🟢 MARKET"
            print(f"\n{idx}. {wallet_status} | {card_data['provider']} {card_data['card_name']}")
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
            all_cards = session.exec(cards_statement).all()
            wallet_cards = [c for c in all_cards if c.is_in_user_wallet]
            market_cards = [c for c in all_cards if not c.is_in_user_wallet]
            
            rules_statement = select(RewardRule)
            rules_count = len(session.exec(rules_statement).all())
            
            txn_statement = select(Transaction).where(Transaction.card_id == zolve_card_id)
            txn_count = len(session.exec(txn_statement).all())
            
            print(f"\n✅ {len(all_cards)} total cards created")
            print(f"   🔵 {len(wallet_cards)} wallet cards (is_in_user_wallet=True)")
            print(f"   🟢 {len(market_cards)} market cards (is_in_user_wallet=False)")
            print(f"✅ {rules_count} reward rules configured")
            print(f"✅ {txn_count} transactions set to Zolve US (suboptimal)")
            print(f"\n🎯 Ready to run optimizer: POST /optimize")
            print(f"   Expected: Optimizer will scan all 10 cards for market winner!\n")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    exit(main())

