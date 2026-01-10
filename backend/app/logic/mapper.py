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
        # All restaurant, coffee shop, bar, and food service purchases
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
        # Supermarkets, grocery stores, and food purchases for home consumption
        grocery_detailed = [
            "FOOD_AND_DRINK_GROCERIES",
            "GENERAL_MERCHANDISE_SUPERSTORES",  # Walmart, Target grocery sections
            "GENERAL_MERCHANDISE_CONVENIENCE_STORES",  # Often codes as grocery
        ]
        for category in grocery_detailed:
            self.detailed_to_bucket[category] = RewardBucket.GROCERY
        
        # ========== GAS ==========
        # Gas stations and fuel purchases
        gas_detailed = [
            "TRANSPORTATION_GAS",
        ]
        for category in gas_detailed:
            self.detailed_to_bucket[category] = RewardBucket.GAS
        
        # ========== TRAVEL ==========
        # Flights, hotels, car rentals, rideshares, parking, tolls, transit
        travel_detailed = [
            # Actual travel
            "TRAVEL_FLIGHTS",
            "TRAVEL_LODGING",
            "TRAVEL_RENTAL_CARS",
            "TRAVEL_OTHER_TRAVEL",
            # Transportation that's often part of travel
            "TRANSPORTATION_TAXIS_AND_RIDE_SHARES",  # Uber, Lyft
            "TRANSPORTATION_PUBLIC_TRANSIT",  # Trains, buses, metro
            "TRANSPORTATION_PARKING",  # Airport parking, parking garages
            "TRANSPORTATION_TOLLS",  # Highway tolls
            "TRANSPORTATION_BIKES_AND_SCOOTERS",  # Bike/scooter rentals
            # Related travel services
            "GENERAL_SERVICES_AUTOMOTIVE",  # Car washes, parking services
        ]
        for category in travel_detailed:
            self.detailed_to_bucket[category] = RewardBucket.TRAVEL
        
        # ========== ONLINE_SHOPPING ==========
        # Online retailers, clothing, electronics, books
        online_shopping_detailed = [
            "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES",  # Amazon, eBay
            "GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES",  # Fashion retailers
            "GENERAL_MERCHANDISE_ELECTRONICS",  # Best Buy, electronics stores
            "GENERAL_MERCHANDISE_DISCOUNT_STORES",  # TJ Maxx, Ross
            "GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS",  # Barnes & Noble
            "GENERAL_MERCHANDISE_DEPARTMENT_STORES",  # Macy's, Nordstrom
            "GENERAL_MERCHANDISE_GIFTS_AND_NOVELTIES",  # Gift shops
            "GENERAL_MERCHANDISE_OFFICE_SUPPLIES",  # Staples, Office Depot
            "GENERAL_MERCHANDISE_PET_SUPPLIES",  # Petco, pet stores
            "GENERAL_MERCHANDISE_SPORTING_GOODS",  # Dick's Sporting Goods
        ]
        for category in online_shopping_detailed:
            self.detailed_to_bucket[category] = RewardBucket.ONLINE_SHOPPING
        
        # ========== STREAMING ==========
        # ONLY actual streaming services (Netflix, Spotify, etc.)
        # Note: Very few cards have streaming-specific bonuses
        streaming_detailed = [
            "ENTERTAINMENT_TV_AND_MOVIES",  # Netflix, Hulu, Disney+
            "ENTERTAINMENT_MUSIC_AND_AUDIO",  # Spotify, Apple Music
        ]
        for category in streaming_detailed:
            self.detailed_to_bucket[category] = RewardBucket.STREAMING
        
        # ========== WHOLESALE ==========
        # Note: Superstores already mapped to GROCERY above
        # True wholesale clubs (Costco, Sam's Club) would go here if identifiable
        
        # ========== DRUGSTORE ==========
        # Pharmacies and medical supplies
        drugstore_detailed = [
            "MEDICAL_PHARMACIES_AND_SUPPLEMENTS",  # CVS, Walgreens, prescriptions
        ]
        for category in drugstore_detailed:
            self.detailed_to_bucket[category] = RewardBucket.DRUGSTORE
        
        # ========== UTILITIES ==========
        # Recurring utility bills and home services
        utilities_detailed = [
            "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY",
            "RENT_AND_UTILITIES_INTERNET_AND_CABLE",
            "RENT_AND_UTILITIES_TELEPHONE",  # Phone bills
            "RENT_AND_UTILITIES_WATER",
            "RENT_AND_UTILITIES_SEWAGE_AND_WASTE_MANAGEMENT",
            "RENT_AND_UTILITIES_OTHER_UTILITIES",
            "GENERAL_SERVICES_POSTAGE_AND_SHIPPING",  # Shipping services
            "HOME_IMPROVEMENT_SECURITY",  # Home security systems
            "GENERAL_SERVICES_INSURANCE",  # Insurance payments
        ]
        for category in utilities_detailed:
            self.detailed_to_bucket[category] = RewardBucket.UTILITIES
        
        # ========== PRIMARY CATEGORY FALLBACKS ==========
        # If detailed category doesn't match, try these primary categories
        self.primary_to_bucket["FOOD_AND_DRINK"] = RewardBucket.DINING
        self.primary_to_bucket["TRANSPORTATION"] = RewardBucket.TRAVEL  # All transportation → travel
        self.primary_to_bucket["TRAVEL"] = RewardBucket.TRAVEL
        self.primary_to_bucket["ENTERTAINMENT"] = RewardBucket.GENERAL  # FIXED: Most entertainment → general rate
        self.primary_to_bucket["MEDICAL"] = RewardBucket.DRUGSTORE  # Medical expenses → drugstore
        self.primary_to_bucket["RENT_AND_UTILITIES"] = RewardBucket.UTILITIES
        
        # Note: GENERAL_MERCHANDISE, GENERAL_SERVICES, HOME_IMPROVEMENT, PERSONAL_CARE
        # deliberately have NO primary fallback - they go to GENERAL unless specifically mapped
    
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

