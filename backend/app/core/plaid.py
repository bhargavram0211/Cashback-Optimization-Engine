"""
GetCardIQ - Plaid Client Configuration
Sub-Phase 1.4: Plaid API client initialization and utilities
"""

import os
from typing import Optional

import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.products import Products


def get_plaid_client() -> plaid_api.PlaidApi:
    """
    Initialize and return a Plaid API client.
    
    Configuration is loaded from environment variables:
    - PLAID_CLIENT_ID: Your Plaid client ID
    - PLAID_SECRET: Your Plaid secret
    - PLAID_ENV: Environment (sandbox, development, or production)
    
    Returns:
        Configured PlaidApi client instance
    
    Raises:
        ValueError: If required environment variables are missing
    """
    client_id = os.getenv("PLAID_CLIENT_ID")
    secret = os.getenv("PLAID_SECRET")
    environment = os.getenv("PLAID_ENV", "sandbox")
    
    if not client_id:
        raise ValueError("PLAID_CLIENT_ID environment variable is required")
    if not secret:
        raise ValueError("PLAID_SECRET environment variable is required")
    
    # Map environment string to Plaid environment
    env_map = {
        "sandbox": plaid.Environment.Sandbox,
        "development": plaid.Environment.Development,
        "production": plaid.Environment.Production,
    }
    
    plaid_env = env_map.get(environment.lower())
    if not plaid_env:
        raise ValueError(f"Invalid PLAID_ENV: {environment}. Must be sandbox, development, or production")
    
    # Configure Plaid client
    configuration = plaid.Configuration(
        host=plaid_env,
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    
    return client


def get_plaid_environment() -> str:
    """Get the current Plaid environment (sandbox, development, or production)."""
    return os.getenv("PLAID_ENV", "sandbox").lower()


# Singleton instance
_plaid_client: Optional[plaid_api.PlaidApi] = None


def get_plaid_client_instance() -> plaid_api.PlaidApi:
    """
    Get or create singleton Plaid client instance.
    This ensures we only initialize the client once.
    """
    global _plaid_client
    if _plaid_client is None:
        _plaid_client = get_plaid_client()
    return _plaid_client

