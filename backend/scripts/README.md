# Backend Scripts

This directory contains utility scripts for managing the Cashback Optimization Engine backend.

## Card Management

### `import_cards.py` - Data-Driven Card Library Importer

**Purpose**: Import credit card products from YAML files into the database.

**Usage**:
```bash
# Import new cards only (skip existing)
python scripts/import_cards.py

# Update existing cards with new data
python scripts/import_cards.py --update-existing

# Verbose mode (show detailed rule-by-rule logging)
python scripts/import_cards.py --verbose
```

**In Docker**:
```bash
docker exec cashback-backend python scripts/import_cards.py
```

---

### Adding a New Card Product

To add a new credit card to the system:

**1. Create a YAML file** in `backend/data/cards/`

Example: `backend/data/cards/chase_sapphire_preferred.yaml`

```yaml
# Chase Sapphire Preferred Card Definition
# Last Updated: 2026-01-16

provider: Chase
card_name: Sapphire Preferred
base_reward_rate: 1.0
is_available_in_market: true
image_url: https://creditcards.chase.com/.../sapphire-preferred.png
benefits_url: https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred

rewards:
  - bucket: DINING
    multiplier: 3.0
  - bucket: TRAVEL
    multiplier: 2.0
  - bucket: STREAMING
    multiplier: 2.0
  - bucket: GENERAL
    multiplier: 1.0
```

**2. Run the import script**:
```bash
python scripts/import_cards.py
```

**3. Verify** the card was imported:
```bash
docker exec cashback-db psql -U cashback_user -d cashback_db -c \
  "SELECT provider, card_name FROM card_products ORDER BY provider;"
```

---

### YAML Schema Reference

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | Credit card issuer (e.g., "Chase", "American Express") |
| `card_name` | string | Card product name (e.g., "Freedom Unlimited") |
| `rewards` | list | Array of reward rules (see below) |

#### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `base_reward_rate` | number | 1.0 | Default cashback percentage for uncategorized purchases |
| `is_available_in_market` | boolean | true | If false, card is discontinued or unavailable |
| `image_url` | string | null | URL to card image (400x250px recommended) |
| `benefits_url` | string | null | Link to issuer's benefits page |

#### Reward Rules Structure

Each item in the `rewards` list must have:

| Field | Type | Description |
|-------|------|-------------|
| `bucket` | string | Spending category (e.g., "DINING", "TRAVEL", "GROCERY") |
| `multiplier` | number | Cashback percentage for this category |

**Available Buckets**:
- `GENERAL` - All other purchases
- `DINING` - Restaurants and bars
- `GROCERY` - Supermarkets
- `TRAVEL` - Flights, hotels, transit
- `GAS` - Gas stations
- `STREAMING` - Streaming services
- `ONLINE_SHOPPING` - E-commerce
- `DRUGSTORE` - Pharmacies
- `WHOLESALE` - Warehouse clubs (Costco, Sam's Club)

---

## Database Management

### `seed_card_products.py` (DEPRECATED)

⚠️ **This script is deprecated.** Use `import_cards.py` instead.

This script contained hardcoded card data and has been replaced by the data-driven YAML approach.

---

## Plaid Integration

### `generate_plaid_token.py` - Create Plaid Access Tokens

**Purpose**: Generate Plaid Link tokens and access tokens for testing.

**Usage**:
```bash
python scripts/generate_plaid_token.py
```

This script:
1. Creates a test user (or uses existing)
2. Generates a Plaid Link token
3. Exchanges public token for access token
4. Stores the PlaidItem in the database

---

### `acid_test_sync.py` - End-to-End Sync Test

**Purpose**: Test the complete Plaid sync flow.

**Usage**:
```bash
python scripts/acid_test_sync.py
```

Or use the shell wrapper:
```bash
bash scripts/acid_test_sync.sh
```

---

## Category Mapping

### `update_buckets.py` - Update Transaction Categories

**Purpose**: Re-run the category normalization logic on existing transactions.

**Usage**:
```bash
python scripts/update_buckets.py
```

Useful when:
- You update the PFC taxonomy mappings
- You want to recategorize historical transactions

---

### `audit_mappings.py` - Audit Category Mappings

**Purpose**: Analyze which Plaid categories are mapped to which internal buckets.

**Usage**:
```bash
python scripts/audit_mappings.py
```

Generates a report showing:
- PFC category → Internal bucket mappings
- Unmapped categories
- Coverage statistics

---

## Archive

The `archive/` directory contains obsolete scripts kept for reference:

- `seed_poc_cards.py.OBSOLETE` - Old PoC seeding script (replaced by data-driven approach)

---

## Development Tips

### Reset Database for Fresh Testing

```bash
# Stop containers
docker-compose down

# Remove database volume
docker volume rm cashback-optimization-engine_postgres_data

# Rebuild and start
docker-compose up -d --build

# Import cards
docker exec cashback-backend python scripts/import_cards.py

# Create test user and sync
docker exec cashback-backend python scripts/generate_plaid_token.py
```

### Check Script Logs

```bash
# Backend logs
docker logs cashback-backend -f

# Database logs
docker logs cashback-db -f
```

---

## Script Dependencies

All scripts require:
- Database connection (via `app.core.database`)
- SQLModel models (via `app.models`)
- Python 3.11+
- Dependencies from `requirements.txt`

When adding new scripts:
1. Add shebang: `#!/usr/bin/env python3`
2. Include docstring with usage examples
3. Add to this README
4. Handle errors gracefully with try/except
5. Provide clear success/failure messages
