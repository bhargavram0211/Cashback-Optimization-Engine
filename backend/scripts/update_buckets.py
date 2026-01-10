#!/usr/bin/env python3
"""
Update internal_bucket for all transactions based on updated mapper.
Run this after changing the category mappings.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models import Transaction
from app.logic import get_mapper


def main():
    print("🔄 Updating internal_bucket for all transactions...")
    print("="*70)
    
    mapper = get_mapper()
    
    with Session(engine) as session:
        # Get all transactions
        statement = select(Transaction)
        transactions = session.exec(statement).all()
        
        if not transactions:
            print("⚠️  No transactions found in database.")
            return 0
        
        print(f"Found {len(transactions)} transactions to update\n")
        
        updated_count = 0
        changes = {}
        
        for txn in transactions:
            # Get new internal bucket
            old_bucket = txn.internal_bucket
            new_bucket = mapper.get_internal_bucket(
                txn.plaid_primary_category,
                txn.plaid_detailed_category
            )
            
            if old_bucket != new_bucket.value:
                txn.internal_bucket = new_bucket.value
                updated_count += 1
                
                # Track changes
                change_key = f"{old_bucket} → {new_bucket.value}"
                changes[change_key] = changes.get(change_key, 0) + 1
        
        # Commit all changes
        session.commit()
        
        print(f"✅ Updated {updated_count} transactions\n")
        
        if changes:
            print("Changes made:")
            for change, count in sorted(changes.items(), key=lambda x: -x[1]):
                print(f"  • {change}: {count} transactions")
        else:
            print("No changes needed - all transactions already have correct buckets!")
        
        print("\n" + "="*70)
        print("✅ Update complete!")
        
        return 0


if __name__ == "__main__":
    exit(main())

