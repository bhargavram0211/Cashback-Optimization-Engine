#!/usr/bin/env python3
"""
Category Mapping Audit Script
Analyzes coverage of the NormalizationMapper against all Plaid PFCv2 categories.

Usage:
    python scripts/audit_mappings.py
    
Output:
    - Summary statistics for each reward bucket
    - List of categories falling back to GENERAL
    - List of categories using Tier 2 (Primary) fallback
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logic import get_mapper, RewardBucket


def load_plaid_categories(csv_path: Path) -> List[Tuple[str, str]]:
    """
    Load all Plaid PFCv2 categories from the CSV file.
    
    Args:
        csv_path: Path to the pfc-taxonomy-all.csv file
    
    Returns:
        List of (primary_category, detailed_category) tuples
    """
    categories = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Skip header rows
        next(reader)  # Header
        next(reader)  # Note about PFCv2/PFCv1
        
        for row in reader:
            if len(row) >= 2 and row[0] and row[1]:
                primary = row[0].strip()
                detailed = row[1].strip()
                if primary and detailed:
                    categories.append((primary, detailed))
    
    return categories


def audit_mappings(csv_path: Path) -> None:
    """
    Audit the NormalizationMapper against all Plaid categories.
    
    Args:
        csv_path: Path to the pfc-taxonomy-all.csv file
    """
    # Load categories and initialize mapper
    print("🔍 Loading Plaid PFCv2 categories...")
    categories = load_plaid_categories(csv_path)
    print(f"   Found {len(categories)} category pairs\n")
    
    mapper = get_mapper()
    print(f"📊 Mapper Statistics:")
    print(f"   - Detailed mappings: {len(mapper.detailed_to_bucket)}")
    print(f"   - Primary fallbacks: {len(mapper.primary_to_bucket)}")
    print()
    
    # Track results
    bucket_counts: Dict[str, int] = defaultdict(int)
    general_fallbacks: List[Tuple[str, str]] = []
    primary_fallbacks: List[Tuple[str, str, str]] = []
    detailed_matches: List[Tuple[str, str, str]] = []
    
    # Process each category
    print("🔄 Processing categories...")
    for primary, detailed in categories:
        bucket = mapper.get_internal_bucket(primary, detailed)
        bucket_counts[bucket.value] += 1
        
        # Determine which tier was used
        if detailed in mapper.detailed_to_bucket:
            # Tier 1: Detailed match
            detailed_matches.append((primary, detailed, bucket.value))
        elif primary in mapper.primary_to_bucket:
            # Tier 2: Primary fallback
            primary_fallbacks.append((primary, detailed, bucket.value))
        else:
            # Tier 3: General default
            general_fallbacks.append((primary, detailed))
    
    print("✅ Processing complete!\n")
    
    # Print summary
    print("=" * 80)
    print("📈 MAPPING SUMMARY")
    print("=" * 80)
    print()
    
    print("Reward Bucket Distribution:")
    print("-" * 80)
    total_mapped = sum(bucket_counts.values())
    for bucket in RewardBucket:
        count = bucket_counts[bucket.value]
        percentage = (count / total_mapped * 100) if total_mapped > 0 else 0
        print(f"  {bucket.value:20s}: {count:3d} categories ({percentage:5.1f}%)")
    print(f"  {'TOTAL':20s}: {total_mapped:3d} categories")
    print()
    
    # Tier statistics
    print("Tier Usage:")
    print("-" * 80)
    print(f"  Tier 1 (Detailed):  {len(detailed_matches):3d} categories ({len(detailed_matches)/total_mapped*100:5.1f}%)")
    print(f"  Tier 2 (Primary):   {len(primary_fallbacks):3d} categories ({len(primary_fallbacks)/total_mapped*100:5.1f}%)")
    print(f"  Tier 3 (General):   {len(general_fallbacks):3d} categories ({len(general_fallbacks)/total_mapped*100:5.1f}%)")
    print()
    
    # General fallbacks (categories we don't handle specifically)
    if general_fallbacks:
        print("=" * 80)
        print(f"⚠️  CATEGORIES FALLING BACK TO GENERAL ({len(general_fallbacks)} total)")
        print("=" * 80)
        print()
        
        # Group by primary category for easier reading
        by_primary: Dict[str, List[str]] = defaultdict(list)
        for primary, detailed in general_fallbacks:
            by_primary[primary].append(detailed)
        
        for primary in sorted(by_primary.keys()):
            print(f"📁 {primary} ({len(by_primary[primary])} categories):")
            for detailed in sorted(by_primary[primary]):
                print(f"   - {detailed}")
            print()
    else:
        print("✅ All categories have specific mappings (no GENERAL fallbacks)\n")
    
    # Primary fallbacks (using Tier 2)
    if primary_fallbacks:
        print("=" * 80)
        print(f"📋 CATEGORIES USING PRIMARY FALLBACK ({len(primary_fallbacks)} total)")
        print("=" * 80)
        print()
        
        # Group by result bucket
        by_bucket: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for primary, detailed, bucket in primary_fallbacks:
            by_bucket[bucket].append((primary, detailed))
        
        for bucket in sorted(by_bucket.keys()):
            print(f"→ {bucket} ({len(by_bucket[bucket])} categories):")
            for primary, detailed in sorted(by_bucket[bucket]):
                print(f"   {primary} / {detailed}")
            print()
    else:
        print("✅ All categories use detailed mappings (no primary fallbacks)\n")
    
    # Detailed matches summary
    print("=" * 80)
    print(f"✓ CATEGORIES WITH DETAILED MAPPINGS ({len(detailed_matches)} total)")
    print("=" * 80)
    print()
    
    # Group by result bucket
    by_bucket_detailed: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for primary, detailed, bucket in detailed_matches:
        by_bucket_detailed[bucket].append((primary, detailed))
    
    for bucket in sorted(by_bucket_detailed.keys()):
        count = len(by_bucket_detailed[bucket])
        print(f"→ {bucket}: {count} categories")
    print()
    
    # Coverage analysis
    print("=" * 80)
    print("📊 COVERAGE ANALYSIS")
    print("=" * 80)
    print()
    
    coverage_pct = ((total_mapped - len(general_fallbacks)) / total_mapped * 100) if total_mapped > 0 else 0
    print(f"Coverage (non-GENERAL): {coverage_pct:.1f}%")
    print(f"  - Specific mappings: {len(detailed_matches)} categories")
    print(f"  - Primary fallbacks: {len(primary_fallbacks)} categories")
    print(f"  - GENERAL defaults:  {len(general_fallbacks)} categories")
    print()
    
    if coverage_pct < 50:
        print("⚠️  WARNING: Less than 50% coverage. Consider adding more mappings.")
    elif coverage_pct < 75:
        print("ℹ️  INFO: Coverage is moderate. Could benefit from additional mappings.")
    else:
        print("✅ Good coverage! Most categories have specific mappings.")
    print()


def main():
    """Main entry point."""
    # Find the CSV file
    script_dir = Path(__file__).parent
    csv_path = script_dir.parent / "app" / "logic" / "pfc-taxonomy-all.csv"
    
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║              PLAID CATEGORY MAPPING AUDIT                                  ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        audit_mappings(csv_path)
    except Exception as e:
        print(f"❌ Error during audit: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 80)
    print("✅ Audit complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

