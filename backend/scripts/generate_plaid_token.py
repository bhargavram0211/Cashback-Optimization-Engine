#!/usr/bin/env python3
"""
Generate a Plaid Sandbox access token for testing.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.plaid import get_plaid_client_instance
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products

def main():
    print("🔑 Generating Plaid Sandbox Access Token...\n")
    
    try:
        # Get Plaid client
        plaid_client = get_plaid_client_instance()
        
        # Step 1: Create sandbox public token
        print("Step 1: Creating public token...")
        public_token_request = SandboxPublicTokenCreateRequest(
            institution_id="ins_109508",  # First Platypus Bank
            initial_products=[Products("transactions"), Products("liabilities")]
        )
        public_token_response = plaid_client.sandbox_public_token_create(public_token_request)
        public_token = public_token_response['public_token']
        print(f"✅ Public token: {public_token}\n")
        
        # Step 2: Exchange for access token
        print("Step 2: Exchanging for access token...")
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        exchange_response = plaid_client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']
        
        print(f"✅ Access token: {access_token}")
        print(f"✅ Item ID: {item_id}\n")
        
        print("="*70)
        print("SUCCESS! Use this access token to create a PlaidItem:")
        print("="*70)
        print(f"\nAccess Token: {access_token}\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

