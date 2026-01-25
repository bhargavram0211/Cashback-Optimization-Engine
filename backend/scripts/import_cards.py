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
from typing import Dict, List, Optional, Tuple
import yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models import CardProduct, RewardRule, UserCard, Transaction


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
    
    YAML-filename-based system: Each YAML file = One Card.
    Cards are identified by yaml_filename, not provider + card_name.
    
    Args:
        session: Database session
        card_data: Validated card data from YAML
        yaml_filename: Name of the YAML file (e.g., "icici_international.yaml")
        update_existing: Whether to update existing cards (always True in new system)
        verbose: Whether to show detailed logging
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    provider = card_data['provider']
    card_name = card_data['card_name']
    
    # PRIMARY LOOKUP: Find card by yaml_filename (not provider + card_name)
    existing = session.exec(
        select(CardProduct).where(CardProduct.yaml_filename == yaml_filename)
    ).first()
    
    # Prepare card product data
    base_reward_rate = Decimal(str(card_data.get('base_reward_rate', 1.0)))
    is_available = card_data.get('is_available_in_market', True)
    image_url = card_data.get('image_url')
    benefits_url = card_data.get('benefits_url')
    
    if existing:
        # UPDATE existing card (yaml_filename matches)
        card_product = existing
        # Update ALL fields, including card_name (handles renames)
        if card_product.card_name != card_name:
            if verbose:
                print(f"      ↻ Renaming: '{card_product.card_name}' → '{card_name}'")
        card_product.provider = provider
        card_product.card_name = card_name
        card_product.base_reward_rate = base_reward_rate
        card_product.is_available_in_market = is_available
        card_product.image_url = image_url
        card_product.benefits_url = benefits_url
        # Ensure yaml_filename is set (in case it was NULL from migration)
        if not card_product.yaml_filename:
            card_product.yaml_filename = yaml_filename
        action = "updated"
    else:
        # CREATE new card (yaml_filename not found)
        card_product = CardProduct(
            provider=provider,
            card_name=card_name,
            base_reward_rate=base_reward_rate,
            is_available_in_market=is_available,
            image_url=image_url,
            benefits_url=benefits_url,
            yaml_filename=yaml_filename  # Set the unique identifier
        )
        session.add(card_product)
        action = "created"
    
    session.commit()
    session.refresh(card_product)
    
    # Always update reward rules: Delete old rules, create new ones from YAML
    # This ensures rules always match the YAML file exactly
    existing_rules = session.exec(
        select(RewardRule).where(RewardRule.card_product_id == card_product.id)
    ).all()
    
    # Delete all existing rules
    for rule in existing_rules:
        session.delete(rule)
    session.commit()
    
    # Create new rules from YAML
    rules_created = 0
    for rule_data in card_data['rewards']:
        bucket = rule_data['bucket'].upper()  # Normalize to uppercase
        multiplier = Decimal(str(rule_data['multiplier']))
        
        new_rule = RewardRule(
            card_product_id=card_product.id,
            bucket=bucket,
            multiplier=multiplier
        )
        session.add(new_rule)
        rules_created += 1
        if verbose:
            print(f"      ✓ Rule: {bucket} → {multiplier}x")
    
    session.commit()
    
    # Build summary message
    if action == "created":
        msg = f"✅ Created with {rules_created} reward rules"
    else:
        msg = f"🔄 Updated with {rules_created} reward rules"
    
    return (True, msg)


def cleanup_orphaned_cards(
    session: Session,
    imported_yaml_filenames: List[str],
    verbose: bool = False
) -> int:
    """
    Delete cards whose YAML files no longer exist.
    
    In the YAML-filename-based system, if a YAML file is deleted, the card should be deleted.
    This ensures the database only contains cards that have corresponding YAML files.
    
    Args:
        session: Database session
        imported_yaml_filenames: List of YAML filenames that were successfully imported
        verbose: Whether to show detailed logging
        
    Returns:
        Number of cards deleted
    """
    if not imported_yaml_filenames:
        return 0
    
    # Get all cards that have a yaml_filename set
    all_cards_with_filename = session.exec(
        select(CardProduct).where(CardProduct.yaml_filename.isnot(None))
    ).all()
    
    # Create set of imported yaml_filenames for fast lookup
    imported_set = set(imported_yaml_filenames)
    
    orphaned_count = 0
    for card in all_cards_with_filename:
        if card.yaml_filename not in imported_set:
            # Check if any UserCards reference this card
            user_cards_using_this = session.exec(
                select(UserCard).where(UserCard.card_product_id == card.id)
            ).all()
            
            # Check if any Transactions reference this card via market_winner_product_id
            transactions_with_market_winner = session.exec(
                select(Transaction).where(Transaction.market_winner_product_id == card.id)
            ).all()
            
            # Update transactions that reference this card as market_winner_product_id
            # NULL out the reference so transactions don't point to deleted/unavailable cards
            if transactions_with_market_winner:
                from decimal import Decimal
                for transaction in transactions_with_market_winner:
                    transaction.market_winner_product_id = None
                    transaction.market_winner_cashback = None
                    session.add(transaction)
                if verbose:
                    print(f"   🔄 Updated {len(transactions_with_market_winner)} transaction(s) with NULL market_winner_product_id")
                session.flush()  # Ensure updates are written
            
            if len(user_cards_using_this) > 0:
                # Can't delete - has UserCard references
                # Mark as unavailable instead
                if card.is_available_in_market:
                    card.is_available_in_market = False
                    session.add(card)
                    session.flush()  # Ensure the change is written
                    orphaned_count += 1
                    if verbose:
                        print(f"   ⚠️  Marked as unavailable (has {len(user_cards_using_this)} user card reference(s)): {card.provider} {card.card_name}")
            else:
                # Safe to delete - no UserCard references (market_winner references already NULLed)
                # First delete reward rules
                rules = session.exec(
                    select(RewardRule).where(RewardRule.card_product_id == card.id)
                ).all()
                for rule in rules:
                    session.delete(rule)
                session.flush()  # Ensure rules are deleted before deleting card
                
                # Then delete the card
                session.delete(card)
                session.flush()  # Ensure card deletion is written
                orphaned_count += 1
                if verbose:
                    print(f"   🗑️  Deleted: {card.provider} {card.card_name} (YAML file removed)")
    
    if orphaned_count > 0:
        session.commit()
    
    return orphaned_count


def migrate_existing_cards(session: Session, yaml_files: List[Path], verbose: bool = False) -> dict:
    """
    Migrate existing cards to have yaml_filename populated.
    
    For cards without yaml_filename, try to match them to YAML files by:
    1. Provider + card_name pattern matching
    2. If no match found, leave as NULL (will be handled on next import)
    
    Args:
        session: Database session
        yaml_files: List of YAML file paths
        verbose: Whether to show detailed logging
        
    Returns:
        Dictionary with migration statistics
    """
    # Get all cards without yaml_filename
    cards_without_filename = session.exec(
        select(CardProduct).where(CardProduct.yaml_filename.is_(None))
    ).all()
    
    if not cards_without_filename:
        return {"migrated": 0, "skipped": 0}
    
    if verbose:
        print(f"\n🔄 Migrating {len(cards_without_filename)} existing card(s) to yaml_filename system...")
    
    migrated = 0
    skipped = 0
    
    # Build a map of (provider, card_name) -> yaml_filename from YAML files
    yaml_map = {}
    for yaml_path in yaml_files:
        try:
            card_data = load_card_from_yaml(yaml_path)
            key = (card_data['provider'], card_data['card_name'])
            yaml_map[key] = yaml_path.name
        except Exception:
            # Skip invalid YAML files
            continue
    
    # Try to match existing cards to YAML files
    for card in cards_without_filename:
        key = (card.provider, card.card_name)
        if key in yaml_map:
            card.yaml_filename = yaml_map[key]
            session.add(card)
            migrated += 1
            if verbose:
                print(f"   ✓ Migrated: {card.provider} {card.card_name} → {yaml_map[key]}")
        else:
            # Try fuzzy matching by normalizing names
            # e.g., "ICICI International" might match "icici_international.yaml"
            card_name_normalized = card.card_name.lower().replace(' ', '_')
            provider_normalized = card.provider.lower().replace(' ', '_')
            
            # Try to find matching YAML file by filename pattern
            matched = False
            for yaml_path in yaml_files:
                filename_stem = yaml_path.stem.lower()
                # Check if provider and card_name appear in filename
                if provider_normalized in filename_stem and card_name_normalized in filename_stem:
                    try:
                        card_data = load_card_from_yaml(yaml_path)
                        # Double-check it's actually the same card
                        if (card_data['provider'] == card.provider and 
                            card_data['card_name'] == card.card_name):
                            card.yaml_filename = yaml_path.name
                            session.add(card)
                            migrated += 1
                            matched = True
                            if verbose:
                                print(f"   ✓ Migrated (fuzzy): {card.provider} {card.card_name} → {yaml_path.name}")
                            break
                    except Exception:
                        continue
            
            if not matched:
                skipped += 1
                if verbose:
                    print(f"   ⏭️  Skipped: {card.provider} {card.card_name} (no matching YAML file)")
    
    if migrated > 0:
        session.commit()
    
    return {"migrated": migrated, "skipped": skipped}


def import_all_cards(
    update_existing: bool = False,
    verbose: bool = False,
    cleanup_orphans: bool = True
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
        "orphaned": 0,
        "migrated": 0,
        "errors": []
    }
    
    imported_yaml_filenames = []  # Track yaml_filenames for cleanup
    
    with Session(engine) as session:
        # First, migrate existing cards without yaml_filename
        migration_stats = migrate_existing_cards(session, yaml_files, verbose)
        stats["migrated"] = migration_stats["migrated"]
        if migration_stats["migrated"] > 0:
            print(f"\n✅ Migrated {migration_stats['migrated']} existing card(s) to yaml_filename system")
        
        for idx, yaml_path in enumerate(yaml_files, start=1):
            try:
                print(f"{idx}. {yaml_path.stem}")
                
                # Load and validate YAML
                card_data = load_card_from_yaml(yaml_path)
                
                # Import to database (always updates if yaml_filename matches)
                success, message = import_card(
                    session,
                    card_data,
                    yaml_path.name,
                    update_existing=True,  # Always update in new system
                    verbose=verbose
                )
                
                print(f"   {message}")
                
                # Track imported yaml_filenames for cleanup
                imported_yaml_filenames.append(yaml_path.name)
                
                stats["success"] += 1
                
            except CardImportError as e:
                print(f"   ❌ Import failed: {e}")
                stats["failed"] += 1
                stats["errors"].append(f"{yaml_path.name}: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                stats["failed"] += 1
                stats["errors"].append(f"{yaml_path.name}: {e}")
        
        # Always cleanup orphaned cards (cards whose YAML files no longer exist)
        print("\n🧹 Cleaning up orphaned cards...")
        orphaned_count = cleanup_orphaned_cards(session, imported_yaml_filenames, verbose)
        stats["orphaned"] = orphaned_count
        if orphaned_count > 0:
            print(f"   Processed {orphaned_count} orphaned card(s)")
        else:
            print(f"   No orphaned cards found")
    
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
    if stats.get('migrated', 0) > 0:
        print(f"   🔄 Migrated:      {stats['migrated']}")
    print(f"   ❌ Failed:       {stats['failed']}")
    if stats.get('orphaned', 0) > 0:
        print(f"   🗑️  Orphaned:      {stats['orphaned']}")
    
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
    parser.add_argument(
        '--cleanup-orphans',
        action='store_true',
        help='Mark cards as unavailable if they are not in any YAML file'
    )
    
    args = parser.parse_args()
    
    try:
        stats = import_all_cards(
            update_existing=args.update_existing,
            verbose=args.verbose,
            cleanup_orphans=args.cleanup_orphans
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
