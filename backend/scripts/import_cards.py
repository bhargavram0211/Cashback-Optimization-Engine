#!/usr/bin/env python3
"""
Data-Driven Card Library Importer
Imports card products from YAML files in backend/data/cards/

This replaces the hardcoded seed_card_products.py script with a flexible,
data-driven approach. To add a new card, simply create a YAML file.

Usage:
    python scripts/import_cards.py                    # Import new cards only
    python scripts/import_cards.py --update-existing  # Update existing cards
    python scripts/import_cards.py --verbose          # Show detailed logging
"""

import sys
import os
import argparse
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Optional
import yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models import CardProduct, RewardRule


# Path to card definitions directory
CARDS_DIR = Path(__file__).parent.parent / "data" / "cards"


class CardImportError(Exception):
    """Custom exception for card import errors"""
    pass


def validate_card_data(data: dict, yaml_path: Path) -> None:
    """
    Validate YAML card data structure.
    
    Args:
        data: Parsed YAML data
        yaml_path: Path to YAML file (for error messages)
        
    Raises:
        CardImportError: If validation fails
    """
    # Required top-level fields
    required_fields = ['provider', 'card_name', 'rewards']
    for field in required_fields:
        if field not in data:
            raise CardImportError(
                f"Missing required field '{field}' in {yaml_path.name}"
            )
    
    # Validate provider and card_name are non-empty strings
    if not isinstance(data['provider'], str) or not data['provider'].strip():
        raise CardImportError(
            f"'provider' must be a non-empty string in {yaml_path.name}"
        )
    
    if not isinstance(data['card_name'], str) or not data['card_name'].strip():
        raise CardImportError(
            f"'card_name' must be a non-empty string in {yaml_path.name}"
        )
    
    # Validate base_reward_rate if provided
    if 'base_reward_rate' in data:
        try:
            rate = float(data['base_reward_rate'])
            if rate < 0 or rate > 100:
                raise CardImportError(
                    f"'base_reward_rate' must be between 0 and 100 in {yaml_path.name}"
                )
        except (ValueError, TypeError):
            raise CardImportError(
                f"'base_reward_rate' must be a number in {yaml_path.name}"
            )
    
    # Validate rewards structure
    if not isinstance(data['rewards'], list) or len(data['rewards']) == 0:
        raise CardImportError(
            f"'rewards' must be a non-empty list in {yaml_path.name}"
        )
    
    for idx, rule in enumerate(data['rewards']):
        if not isinstance(rule, dict):
            raise CardImportError(
                f"Reward rule #{idx+1} must be a dictionary in {yaml_path.name}"
            )
        
        if 'bucket' not in rule or 'multiplier' not in rule:
            raise CardImportError(
                f"Reward rule #{idx+1} missing 'bucket' or 'multiplier' in {yaml_path.name}"
            )
        
        if not isinstance(rule['bucket'], str) or not rule['bucket'].strip():
            raise CardImportError(
                f"Reward rule #{idx+1} 'bucket' must be a non-empty string in {yaml_path.name}"
            )
        
        try:
            multiplier = float(rule['multiplier'])
            if multiplier < 0 or multiplier > 100:
                raise CardImportError(
                    f"Reward rule #{idx+1} 'multiplier' must be between 0 and 100 in {yaml_path.name}"
                )
        except (ValueError, TypeError):
            raise CardImportError(
                f"Reward rule #{idx+1} 'multiplier' must be a number in {yaml_path.name}"
            )


def load_card_from_yaml(yaml_path: Path) -> dict:
    """
    Load and validate card data from a YAML file.
    
    Args:
        yaml_path: Path to the YAML file
        
    Returns:
        Dictionary with validated card data
        
    Raises:
        CardImportError: If file can't be read or validation fails
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise CardImportError(f"Invalid YAML syntax in {yaml_path.name}: {e}")
    except Exception as e:
        raise CardImportError(f"Failed to read {yaml_path.name}: {e}")
    
    if not isinstance(data, dict):
        raise CardImportError(f"YAML file {yaml_path.name} must contain a dictionary")
    
    # Validate the structure
    validate_card_data(data, yaml_path)
    
    return data


def import_card(
    session: Session,
    card_data: dict,
    yaml_filename: str,
    update_existing: bool = False,
    verbose: bool = False
) -> tuple[bool, str]:
    """
    Import or update a single card product.
    
    Args:
        session: Database session
        card_data: Validated card data from YAML
        yaml_filename: Name of the YAML file (for logging)
        update_existing: Whether to update existing cards
        verbose: Whether to show detailed logging
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    provider = card_data['provider']
    card_name = card_data['card_name']
    
    # Check if card product already exists (by provider + card_name)
    existing = session.exec(
        select(CardProduct).where(
            CardProduct.provider == provider,
            CardProduct.card_name == card_name
        )
    ).first()
    
    if existing and not update_existing:
        return (True, f"⏭️  Skipped (already exists)")
    
    # Prepare card product data
    base_reward_rate = Decimal(str(card_data.get('base_reward_rate', 1.0)))
    is_available = card_data.get('is_available_in_market', True)
    image_url = card_data.get('image_url')
    benefits_url = card_data.get('benefits_url')
    
    if existing:
        # Update existing card product
        card_product = existing
        card_product.base_reward_rate = base_reward_rate
        card_product.is_available_in_market = is_available
        card_product.image_url = image_url
        card_product.benefits_url = benefits_url
        action = "updated"
    else:
        # Create new card product
        card_product = CardProduct(
            provider=provider,
            card_name=card_name,
            base_reward_rate=base_reward_rate,
            is_available_in_market=is_available,
            image_url=image_url,
            benefits_url=benefits_url
        )
        session.add(card_product)
        action = "created"
    
    session.commit()
    session.refresh(card_product)
    
    # Import reward rules
    rules_processed = 0
    rules_created = 0
    rules_updated = 0
    
    for rule_data in card_data['rewards']:
        bucket = rule_data['bucket'].upper()  # Normalize to uppercase
        multiplier = Decimal(str(rule_data['multiplier']))
        
        # Check if rule exists
        existing_rule = session.exec(
            select(RewardRule).where(
                RewardRule.card_product_id == card_product.id,
                RewardRule.bucket == bucket
            )
        ).first()
        
        if existing_rule:
            if update_existing or not existing:
                existing_rule.multiplier = multiplier
                session.commit()
                rules_updated += 1
                if verbose:
                    print(f"      ↻ Updated: {bucket} → {multiplier}x")
        else:
            new_rule = RewardRule(
                card_product_id=card_product.id,
                bucket=bucket,
                multiplier=multiplier
            )
            session.add(new_rule)
            session.commit()
            rules_created += 1
            if verbose:
                print(f"      ✓ Created: {bucket} → {multiplier}x")
        
        rules_processed += 1
    
    # Build summary message
    if action == "created":
        msg = f"✅ Created with {rules_created} reward rules"
    else:
        msg = f"🔄 Updated ({rules_updated} rules updated, {rules_created} rules added)"
    
    return (True, msg)


def import_all_cards(
    update_existing: bool = False,
    verbose: bool = False
) -> dict:
    """
    Import all card YAML files from the cards directory.
    
    Args:
        update_existing: Whether to update existing cards
        verbose: Whether to show detailed logging
        
    Returns:
        Dictionary with import statistics
    """
    if not CARDS_DIR.exists():
        print(f"\n❌ Cards directory not found: {CARDS_DIR}")
        print(f"   Please create it and add YAML card definitions.")
        return {"success": False, "error": "Directory not found"}
    
    # Find all YAML files
    yaml_files = sorted(CARDS_DIR.glob("*.yaml")) + sorted(CARDS_DIR.glob("*.yml"))
    
    if not yaml_files:
        print(f"\n⚠️  No YAML files found in {CARDS_DIR}")
        return {"success": False, "error": "No YAML files found"}
    
    print("\n" + "=" * 80)
    print("DATA-DRIVEN CARD LIBRARY IMPORT")
    print("=" * 80)
    print(f"\n📁 Source: {CARDS_DIR}")
    print(f"📄 Found {len(yaml_files)} YAML file(s)")
    print(f"🔄 Update mode: {'ON' if update_existing else 'OFF'}")
    print()
    
    stats = {
        "total": len(yaml_files),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    with Session(engine) as session:
        for idx, yaml_path in enumerate(yaml_files, start=1):
            try:
                print(f"{idx}. {yaml_path.stem}")
                
                # Load and validate YAML
                card_data = load_card_from_yaml(yaml_path)
                
                # Import to database
                success, message = import_card(
                    session,
                    card_data,
                    yaml_path.name,
                    update_existing,
                    verbose
                )
                
                print(f"   {message}")
                
                if "Skipped" in message:
                    stats["skipped"] += 1
                else:
                    stats["success"] += 1
                
            except CardImportError as e:
                print(f"   ❌ Import failed: {e}")
                stats["failed"] += 1
                stats["errors"].append(f"{yaml_path.name}: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                stats["failed"] += 1
                stats["errors"].append(f"{yaml_path.name}: {e}")
    
    return stats


def print_summary(stats: dict):
    """Print import summary statistics."""
    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    
    if not stats.get("success", False) and "error" in stats:
        print(f"\n❌ {stats['error']}")
        return
    
    print(f"\n📊 Results:")
    print(f"   Total files:     {stats['total']}")
    print(f"   ✅ Successful:   {stats['success']}")
    print(f"   ⏭️  Skipped:      {stats['skipped']}")
    print(f"   ❌ Failed:       {stats['failed']}")
    
    if stats['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in stats['errors']:
            print(f"   • {error}")
    
    # Query final database state
    with Session(engine) as session:
        total_products = len(session.exec(select(CardProduct)).all())
        total_rules = len(session.exec(select(RewardRule)).all())
        
        print(f"\n📚 Database state:")
        print(f"   {total_products} CardProducts in library")
        print(f"   {total_rules} reward rules configured")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Run Plaid sync to create UserCard instances")
    print(f"   2. Have users identify their cards via /user-cards/.../identify")
    print(f"   3. Run optimizer to calculate rewards")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import credit card products from YAML files"
    )
    parser.add_argument(
        '--update-existing',
        action='store_true',
        help='Update existing cards instead of skipping them'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed logging for each card'
    )
    
    args = parser.parse_args()
    
    try:
        stats = import_all_cards(
            update_existing=args.update_existing,
            verbose=args.verbose
        )
        print_summary(stats)
        
        # Exit with error code if any imports failed
        if stats.get("failed", 0) > 0:
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Import cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
