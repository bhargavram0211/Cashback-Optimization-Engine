"""
Cashback Optimization Engine - Category Normalization Mapper
Sub-Phase 1.3: Maps Plaid's PFCv2 taxonomy to internal reward buckets

Reference: SRS Section 4 - Category Normalization Mapper
"""

import csv
from pathlib import Path
from typing import Dict, Optional
from enum import Enum


class RewardBucket(str, Enum):
    """
    Internal reward buckets for cashback categorization.
    These align with common credit card reward categories.
    """
    DINING = "DINING"
    GROCERY = "GROCERY"
    GAS = "GAS"
    TRAVEL = "TRAVEL"
    ONLINE_SHOPPING = "ONLINE_SHOPPING"
    STREAMING = "STREAMING"
    WHOLESALE = "WHOLESALE"
    DRUGSTORE = "DRUGSTORE"
    UTILITIES = "UTILITIES"
    GENERAL = "GENERAL"


class NormalizationMapper:
    """
    Maps Plaid's PFCv2 categories to internal reward buckets.
    
    Implements a 3-tier fallback strategy:
    1. Try to match the detailed category
    2. Fall back to the primary category
    3. Default to GENERAL if no match
    
    SRS Reference: Section 4.2 - Mapping Logic
    """
    
    def __init__(self, csv_path: Optional[Path] = None):
        """
        Initialize the mapper and load category mappings.
        
        Args:
            csv_path: Path to the PFCv2 taxonomy CSV. If None, uses default location.
        """
        if csv_path is None:
            # Default to the CSV in the same directory
            csv_path = Path(__file__).parent / "pfc-taxonomy-all.csv"
        
        self.csv_path = csv_path
        self.detailed_to_bucket: Dict[str, RewardBucket] = {}
        self.primary_to_bucket: Dict[str, RewardBucket] = {}
        
        # Load the mapping rules
        self._initialize_mappings()
    
    def _initialize_mappings(self) -> None:
        """
        Initialize the mapping dictionaries based on SRS Section 4.2.
        
        Maps Plaid categories to internal reward buckets according to:
        - DINING: Restaurants, coffee shops, fast food
        - GROCERY: Groceries, supermarkets
        - GAS: Gas stations, fuel
        - TRAVEL: Flights, hotels, taxis/rideshares
        - ONLINE_SHOPPING: Online marketplaces
        - STREAMING: TV/movies, music/audio
        - WHOLESALE: Wholesale clubs, superstores
        - DRUGSTORE: Pharmacies and supplements
        - UTILITIES: Gas/electricity, internet/cable, water, phone
        - GENERAL: Everything else
        """
        
        # ========== DINING ==========
        dining_detailed = [
            "FOOD_AND_DRINK_RESTAURANT",
            "FOOD_AND_DRINK_COFFEE",
            "FOOD_AND_DRINK_FAST_FOOD",
            "FOOD_AND_DRINK_BEER_WINE_AND_LIQUOR",
            "FOOD_AND_DRINK_VENDING_MACHINES",
        ]
        for category in dining_detailed:
            self.detailed_to_bucket[category] = RewardBucket.DINING
        
        # ========== GROCERY ==========
        grocery_detailed = [
            "FOOD_AND_DRINK_GROCERIES",
            "GENERAL_MERCHANDISE_SUPERSTORES",  # Walmart, Target, etc.
            "GENERAL_MERCHANDISE_CONVENIENCE_STORES",  # Often codes as grocery/gas
        ]
        for category in grocery_detailed:
            self.detailed_to_bucket[category] = RewardBucket.GROCERY
        
        # ========== GAS ==========
        gas_detailed = [
            "TRANSPORTATION_GAS",
        ]
        for category in gas_detailed:
            self.detailed_to_bucket[category] = RewardBucket.GAS
        
        # ========== TRAVEL ==========
        travel_detailed = [
            "TRAVEL_FLIGHTS",
            "TRAVEL_LODGING",
            "TRAVEL_RENTAL_CARS",
            "TRAVEL_OTHER_TRAVEL",
            "TRANSPORTATION_TAXIS_AND_RIDE_SHARES",
            "GENERAL_SERVICES_AUTOMOTIVE",  # Parking, tolls, car services
            "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS",  # Wellness/travel cards now cover this
        ]
        for category in travel_detailed:
            self.detailed_to_bucket[category] = RewardBucket.TRAVEL
        
        # ========== ONLINE_SHOPPING ==========
        online_shopping_detailed = [
            "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES",
            "GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES",
            "GENERAL_MERCHANDISE_ELECTRONICS",
            "GENERAL_MERCHANDISE_DISCOUNT_STORES",
            "GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS",
        ]
        for category in online_shopping_detailed:
            self.detailed_to_bucket[category] = RewardBucket.ONLINE_SHOPPING
        
        # ========== STREAMING ==========
        streaming_detailed = [
            "ENTERTAINMENT_TV_AND_MOVIES",
            "ENTERTAINMENT_MUSIC_AND_AUDIO",
        ]
        for category in streaming_detailed:
            self.detailed_to_bucket[category] = RewardBucket.STREAMING
        
        # ========== WHOLESALE ==========
        # Note: Superstores mapped to GROCERY above for better cashback alignment
        # Wholesale clubs would go here if we had specific identifiers
        
        # ========== DRUGSTORE ==========
        drugstore_detailed = [
            "MEDICAL_PHARMACIES_AND_SUPPLEMENTS",
        ]
        for category in drugstore_detailed:
            self.detailed_to_bucket[category] = RewardBucket.DRUGSTORE
        
        # ========== UTILITIES ==========
        utilities_detailed = [
            "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY",
            "RENT_AND_UTILITIES_INTERNET_AND_CABLE",
            "RENT_AND_UTILITIES_TELEPHONE",
            "RENT_AND_UTILITIES_WATER",
            "RENT_AND_UTILITIES_SEWAGE_AND_WASTE_MANAGEMENT",
            "RENT_AND_UTILITIES_OTHER_UTILITIES",
            "GENERAL_SERVICES_POSTAGE_AND_SHIPPING",  # Utility-like recurring service
            "HOME_IMPROVEMENT_SECURITY",  # Home security systems (utilities category)
        ]
        for category in utilities_detailed:
            self.detailed_to_bucket[category] = RewardBucket.UTILITIES
        
        # ========== PRIMARY CATEGORY FALLBACKS ==========
        # If detailed category doesn't match, try these primary categories
        self.primary_to_bucket["FOOD_AND_DRINK"] = RewardBucket.DINING
        self.primary_to_bucket["TRANSPORTATION"] = RewardBucket.TRAVEL  # Trains, buses, public transit
        self.primary_to_bucket["TRAVEL"] = RewardBucket.TRAVEL
        self.primary_to_bucket["ENTERTAINMENT"] = RewardBucket.STREAMING
        self.primary_to_bucket["MEDICAL"] = RewardBucket.DRUGSTORE  # Doctor visits, pharmacies
        self.primary_to_bucket["RENT_AND_UTILITIES"] = RewardBucket.UTILITIES
    
    def get_internal_bucket(
        self, 
        primary_category: Optional[str], 
        detailed_category: Optional[str]
    ) -> RewardBucket:
        """
        Map Plaid categories to internal reward bucket using 3-tier fallback.
        
        Tier 1: Try to match the detailed category
        Tier 2: Fall back to the primary category
        Tier 3: Default to GENERAL
        
        Args:
            primary_category: Plaid's primary category (e.g., "FOOD_AND_DRINK")
            detailed_category: Plaid's detailed category (e.g., "FOOD_AND_DRINK_RESTAURANT")
        
        Returns:
            RewardBucket enum value
        
        Examples:
            >>> mapper = NormalizationMapper()
            >>> mapper.get_internal_bucket("FOOD_AND_DRINK", "FOOD_AND_DRINK_RESTAURANT")
            RewardBucket.DINING
            
            >>> mapper.get_internal_bucket("FOOD_AND_DRINK", "FOOD_AND_DRINK_OTHER_FOOD_AND_DRINK")
            RewardBucket.DINING  # Falls back to primary
            
            >>> mapper.get_internal_bucket("GENERAL_SERVICES", "GENERAL_SERVICES_ACCOUNTING")
            RewardBucket.GENERAL  # No match, defaults to GENERAL
        """
        # Tier 1: Try detailed category (most specific)
        if detailed_category and detailed_category in self.detailed_to_bucket:
            return self.detailed_to_bucket[detailed_category]
        
        # Tier 2: Fall back to primary category
        if primary_category and primary_category in self.primary_to_bucket:
            return self.primary_to_bucket[primary_category]
        
        # Tier 3: Default to GENERAL
        return RewardBucket.GENERAL
    
    def get_bucket_stats(self) -> Dict[str, int]:
        """
        Get statistics about the current mappings.
        Useful for debugging and validation.
        
        Returns:
            Dictionary with counts of mappings per bucket
        """
        stats = {bucket.value: 0 for bucket in RewardBucket}
        
        # Count detailed mappings
        for bucket in self.detailed_to_bucket.values():
            stats[bucket.value] += 1
        
        return stats
    
    def __repr__(self) -> str:
        """String representation showing mapping counts."""
        detailed_count = len(self.detailed_to_bucket)
        primary_count = len(self.primary_to_bucket)
        return (
            f"NormalizationMapper("
            f"detailed_mappings={detailed_count}, "
            f"primary_mappings={primary_count})"
        )


# Singleton instance for easy import
_mapper_instance: Optional[NormalizationMapper] = None


def get_mapper() -> NormalizationMapper:
    """
    Get or create the singleton mapper instance.
    This ensures we only load the CSV once.
    """
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = NormalizationMapper()
    return _mapper_instance

