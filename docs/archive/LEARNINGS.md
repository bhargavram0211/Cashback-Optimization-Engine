# Project Learnings & Troubleshooting Guide

> **Historical Document** - This document is preserved for reference. It contains troubleshooting notes from early development phases (Sub-Phases 1.1-1.4). Some information may be outdated. For current troubleshooting, see [DOCKER_GUIDE.md](../../DOCKER_GUIDE.md) and [DEPLOYMENT.md](../../DEPLOYMENT.md).

This document captures issues encountered during development, their root causes, and solutions. It serves as a knowledge base for future development and debugging.

---

## Table of Contents
- [Sub-Phase 1.1: Infrastructure Shell](#sub-phase-11-infrastructure-shell)
- [Sub-Phase 1.2: Data Models](#sub-phase-12-data-models)
- [Sub-Phase 1.3: Category Mapper](#sub-phase-13-category-mapper)
- [Sub-Phase 1.4: Sync Engine](#sub-phase-14-sync-engine)

---

## Sub-Phase 1.1: Infrastructure Shell

### Issue 1: PostgreSQL Authentication Failed

**Date:** 2026-01-04  
**Phase:** Infrastructure Setup  
**Symptom:**
```
password authentication failed for user "cashback_user"
```

**Root Cause:**  
PostgreSQL volume from a previous run (January 2nd) still existed with different credentials. When PostgreSQL finds an existing database volume, it **skips initialization** and retains the old credentials.

**Error Details:**
- Log message: `PostgreSQL Database directory appears to contain a database; Skipping initialization`
- The database was using old credentials, but the backend was trying to connect with new ones from `.env`

**Solution:**
```bash
docker-compose down -v  # The -v flag removes volumes
docker-compose up -d
```

**Key Learning:**
> ⚠️ **IMPORTANT:** Whenever you change database credentials in `.env`, you MUST remove the old PostgreSQL volume. The `-v` flag in `docker-compose down` is critical for fresh starts.

**Best Practice:**
- Always use `docker-compose down -v` when changing database configurations
- Document this in README for other developers

---

## Sub-Phase 1.2: Data Models

### Issue 2: RecursionError During Model Import

**Date:** 2026-01-04  
**Phase:** SQLModel Table Definitions  
**Symptom:**
```python
RecursionError: maximum recursion depth exceeded
# Occurred in pydantic/_internal/_repr.py during schema generation
```

**Root Cause:**  
The "Deferred Identity" loop in Pydantic v2. Old versions of SQLModel (0.0.14) and Pydantic (2.5.3) had known friction when mixing SQLAlchemy `Column` definitions with Pydantic's `FieldInfo`. The recursion occurred when Pydantic tried to determine the "representation" of the `Transaction` class before the class itself was fully initialized.

**Error Details:**
- Failed at: `class Transaction(SQLModel, table=True):`
- Stack trace showed: `_repr.py` → `display_as_type()` → infinite `repr()` loop
- The issue was particularly prevalent with complex models using `Decimal` types and `Optional[UUID]` fields

**Solution (3-Part Fix):**

**1. Update Dependencies (requirements.txt):**
```python
# OLD (problematic versions)
sqlmodel==0.0.14
pydantic==2.5.3
pydantic-settings==2.1.0

# NEW (stable versions with Pydantic v2 fixes)
sqlmodel>=0.0.22  # Critical update for Pydantic v2 stability
pydantic>=2.7.0   # Improved recursion detection
pydantic-settings>=2.2.1
```

**2. Add model_rebuild() Calls:**
```python
# At the END of app/models/models.py
# Force Pydantic to resolve all forward references after all classes are defined
User.model_rebuild()
PlaidItem.model_rebuild()
Card.model_rebuild()
Transaction.model_rebuild()
```

**3. Use Standard Type Imports:**
```python
# Avoid custom aliases that can confuse Pydantic's _repr logic
from decimal import Decimal  # Good - Pydantic v2 handles this natively

# Don't do this:
from decimal import Decimal as PythonDecimal  # Can confuse the repr logic
```

**Key Learning:**
> 💡 **IMPORTANT:** In Pydantic v2, `model_rebuild()` is the successor to v1's `update_forward_refs()`. It prevents infinite loops by finalizing the schema only when all types are available in the namespace.

**Why This Works:**
- **SQLModel 0.0.22+**: Contains internal fixes specifically for RecursionError when mixing SQLAlchemy Column definitions with Pydantic FieldInfo
- **Pydantic 2.7.0+**: Improved recursion detection in schema generation
- **model_rebuild()**: Stops the `_repr.py` infinite loop by finalizing schemas after all classes are defined

---

### Issue 3: Field Name Clashing with Type Annotation

**Date:** 2026-01-04  
**Phase:** SQLModel Table Definitions  
**Symptom:**
```python
pydantic.errors.PydanticUserError: Error when building FieldInfo from annotated attribute. 
Make sure you don't have any field name clashing with a type annotation.
```

**Root Cause:**  
In the `Transaction` model, the field name `date` clashed with the imported type `date` from `datetime.date`:

```python
from datetime import date  # Type import

class Transaction(SQLModel, table=True):
    date: date = Field(...)  # Field name "date" clashes with type "date"
```

Pydantic v2 is stricter about this and raises an explicit error when field names shadow type annotations.

**Solution:**
```python
# Import with alias to avoid collision
from datetime import date as DateType

class Transaction(SQLModel, table=True):
    date: DateType = Field(nullable=False, index=True)  # No collision
```

**Key Learning:**
> ⚠️ **BEST PRACTICE:** Never name a field the same as its type. Common collisions to avoid:
> - `date: date` → use `date: DateType`
> - `type: type` → use `record_type: str`
> - `list: list` → use `items: list`
> - `dict: dict` → use `mapping: dict`

**Alternative Solutions:**
1. Rename the field: `transaction_date: date`
2. Use type alias: `DateType = date`
3. Use string annotations (less preferred in Pydantic v2)

---

## Sub-Phase 1.3: Category Mapper

### Implementation Summary

**Date:** 2026-01-04  
**Phase:** Category Normalization Logic  
**Status:** ✅ Completed Successfully

**What Was Built:**
- `NormalizationMapper` class in `app/logic/mapper.py`
- 3-tier fallback logic (detailed → primary → GENERAL)
- Mapping for 10 internal reward buckets
- Test endpoint `POST /test-map` for validation

**Key Decisions:**

1. **Enum-Based Reward Buckets**
   - Used Python `Enum` for type safety and autocomplete
   - All 10 buckets defined: DINING, GROCERY, GAS, TRAVEL, ONLINE_SHOPPING, STREAMING, WHOLESALE, DRUGSTORE, UTILITIES, GENERAL

2. **Singleton Pattern for Mapper**
   - `get_mapper()` function ensures only one instance
   - Mapper loads once on startup, cached for all requests
   - Improves performance by avoiding repeated CSV parsing

3. **Explicit Mapping Dictionaries**
   - `detailed_to_bucket`: 23 specific category mappings
   - `primary_to_bucket`: 6 fallback mappings
   - No CSV parsing needed (hardcoded for MVP speed)

**Mapping Statistics:**
```
Detailed mappings: 23
Primary fallbacks: 6
Buckets covered:
  - DINING: 5 categories
  - GROCERY: 2 categories  
  - GAS: 1 category
  - TRAVEL: 5 categories
  - ONLINE_SHOPPING: 1 category
  - STREAMING: 2 categories
  - WHOLESALE: 0 categories (superstores mapped to GROCERY)
  - DRUGSTORE: 1 category
  - UTILITIES: 6 categories
  - GENERAL: 0 explicit (default fallback)
```

**Test Results:**
All 15 test cases passed:
- ✅ Tier 1 (Detailed): DINING, GROCERY, GAS, TRAVEL, STREAMING, ONLINE_SHOPPING, DRUGSTORE, UTILITIES
- ✅ Tier 2 (Primary): Fallback to DINING, UTILITIES
- ✅ Tier 3 (General): Unknown categories default correctly
- ✅ Edge cases: Null inputs, missing categories, rideshares, superstores

**Notable Mapping Decisions:**

| Plaid Category | Internal Bucket | Rationale |
|----------------|-----------------|-----------|
| `TRANSPORTATION_TAXIS_AND_RIDE_SHARES` | TRAVEL | Aligns with travel rewards, not gas |
| `GENERAL_MERCHANDISE_SUPERSTORES` | GROCERY | Better cashback alignment (e.g., Walmart, Target) |
| `FOOD_AND_DRINK_COFFEE` | DINING | Treated as dining out, not grocery |
| `RENT_AND_UTILITIES_INTERNET_AND_CABLE` | UTILITIES | Includes streaming services paid as utilities |

**API Endpoint:**
```bash
POST /test-map
Content-Type: application/json

{
  "primary_category": "FOOD_AND_DRINK",
  "detailed_category": "FOOD_AND_DRINK_RESTAURANT"
}

Response:
{
  "primary_category": "FOOD_AND_DRINK",
  "detailed_category": "FOOD_AND_DRINK_RESTAURANT",
  "internal_bucket": "DINING",
  "tier_used": "detailed"
}
```

**Key Learnings:**

> 💡 **Design Pattern:** The 3-tier fallback provides robustness. Even if Plaid adds new detailed categories, the primary fallback ensures reasonable classification.

> 💡 **Performance:** Singleton pattern with in-memory dictionaries is fast enough for MVP. No need for database lookups or complex caching yet.

> 💡 **Type Safety:** Using Pydantic `BaseModel` for request/response and Python `Enum` for buckets provides excellent validation and autocomplete in IDEs.

**Audit Script Created:**
Created `scripts/audit_mappings.py` to analyze mapping coverage:
- Processes all 123 Plaid PFCv2 categories
- Shows distribution across 10 reward buckets
- Identifies GENERAL fallbacks and primary fallbacks

**Audit Results:**
```
Total categories: 123
Coverage (non-GENERAL): 32.5%
  - Tier 1 (Detailed):  23 categories (18.7%)
  - Tier 2 (Primary):   17 categories (13.8%)
  - Tier 3 (General):   83 categories (67.5%)

Reward Bucket Distribution:
  DINING:          6 categories (4.9%)
  GROCERY:         2 categories (1.6%)
  GAS:             6 categories (4.9%)
  TRAVEL:          5 categories (4.1%)
  ONLINE_SHOPPING: 1 category  (0.8%)
  STREAMING:       6 categories (4.9%)
  DRUGSTORE:       7 categories (5.7%)
  UTILITIES:       7 categories (5.7%)
  GENERAL:        83 categories (67.5%)
```

**Coverage Analysis:**
The 67.5% GENERAL fallback rate is **expected and correct** because:
- ✅ **INCOME** (12 categories): Not spending, correctly → GENERAL
- ✅ **TRANSFERS** (12 categories): Not spending, correctly → GENERAL
- ✅ **LOAN_DISBURSEMENTS/PAYMENTS** (16 categories): Already filtered by SRS, correctly → GENERAL
- ✅ **BANK_FEES** (8 categories): Don't earn rewards, correctly → GENERAL
- ✅ **GENERAL_SERVICES** (9 categories): No specific reward category
- ✅ **GOVERNMENT_AND_NON_PROFIT** (4 categories): No specific reward category

Of the 123 categories, **57 are non-spending categories** that should default to GENERAL.

**Effective Coverage for Spending Categories:**
- Spending categories: ~66 (123 - 57 non-spending)
- Mapped specifically: 40 (23 detailed + 17 primary)
- **Actual coverage: 60.6%** of spending categories

**Potential Improvements Identified:**
1. **Transportation Primary Fallback**: Parking, tolls, public transit → GAS might not be ideal
   - Consider: Separate bucket or different mapping
2. **Medical Primary Fallback**: All medical → DRUGSTORE might confuse users
   - Dental, eye care, primary care aren't pharmacies
3. **Rent → UTILITIES**: Rent falling back to utilities is semantically incorrect
   - Should probably be GENERAL instead

**Sub-Phase 1.3.1: Mapping Optimization**

**Date:** 2026-01-04  
**Goal:** Improve coverage from 60.6% → 74.2% of spending categories

**Changes Made:**

1. **ONLINE_SHOPPING Bucket** (+4 categories):
   - Added: `GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES`
   - Added: `GENERAL_MERCHANDISE_ELECTRONICS`
   - Added: `GENERAL_MERCHANDISE_DISCOUNT_STORES`
   - Added: `GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS`

2. **GROCERY Bucket** (+1 category):
   - Added: `GENERAL_MERCHANDISE_CONVENIENCE_STORES` (commonly codes as grocery/gas)

3. **TRAVEL Bucket** (+2 categories):
   - Added: `GENERAL_SERVICES_AUTOMOTIVE` (parking, tolls, car services)
   - Added: `PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS` (wellness travel cards)

4. **UTILITIES Bucket** (+2 categories):
   - Added: `GENERAL_SERVICES_POSTAGE_AND_SHIPPING`
   - Added: `HOME_IMPROVEMENT_SECURITY` (home security systems)

5. **Primary Fallback Refinement**:
   - Changed: `TRANSPORTATION` primary → `TRAVEL` (was `GAS`)
   - Rationale: Better captures trains, buses, public transit
   - Impact: 5 transportation categories now map to TRAVEL

**Results:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Detailed Mappings | 23 | 32 | +9 (+39%) |
| GENERAL Defaults | 83 | 74 | -9 (-11%) |
| Coverage (non-GENERAL) | 32.5% | 39.8% | +7.3% |
| **Effective Spending Coverage** | **60.6%** | **74.2%** | **+13.6%** |

**Reward Bucket Distribution After Optimization:**
- DINING: 6 categories
- GROCERY: 3 categories (+1)
- GAS: 1 category (-5, moved to TRAVEL)
- TRAVEL: 12 categories (+7)
- ONLINE_SHOPPING: 5 categories (+4)
- STREAMING: 6 categories
- DRUGSTORE: 7 categories
- UTILITIES: 9 categories (+2)
- GENERAL: 74 categories (-9)

**Alignment with 2026 Credit Card Rewards:**
- ✅ Chase Sapphire Reserve: Travel includes transit, parking
- ✅ Amex Gold: Grocery includes convenience stores
- ✅ Capital One Venture X: Wellness/gym as travel benefit
- ✅ Citi Custom Cash: Online shopping as distinct category
- ✅ Blue Cash Preferred: Security systems as utilities

**Future Enhancements:**
- [ ] Add CSV-based configuration for easier updates
- [ ] Add merchant name overrides (e.g., "Costco" → WHOLESALE even if categorized as GROCERY)
- [ ] Add confidence scores for ambiguous mappings
- [ ] Add analytics endpoint to show mapping distribution across actual transactions
- [ ] Consider adding department stores, pet supplies, sporting goods to specific buckets

---

## Sub-Phase 1.4: Sync Engine

### Implementation Summary

**Date:** 2026-01-04  
**Phase:** Plaid Transaction Sync with 3-Stage Filter Pipeline  
**Status:** ✅ Completed Successfully

**What Was Built:**
- Plaid client initialization (`app/core/plaid.py`)
- Transaction sync endpoint (`POST /sync/{item_id}`)
- 3-stage filter pipeline (SRS Section 2.2)
- UPSERT logic with `plaid_transaction_id`
- Cursor-based incremental sync
- Automatic card creation for credit accounts
- Category normalization integration

### Architecture

**Files Created:**

1. **`app/core/plaid.py`** - Plaid client configuration
   - Singleton pattern for client instance
   - Environment-based configuration (sandbox/development/production)
   - Proper credential management from `.env`

2. **`app/core/database.py`** - Database session management
   - Dependency injection with `get_session()`
   - Centralized engine configuration
   - Used with FastAPI's `Depends()` for automatic session management

3. **`app/api/sync.py`** - Sync endpoint implementation
   - `POST /sync/{item_id}` endpoint
   - 3-stage filter pipeline
   - UPSERT logic
   - Cursor management
   - Category normalization

**Files Modified:**
- `requirements.txt` - Added `plaid-python==20.0.0`
- `env.example` - Added Plaid credentials
- `app/main.py` - Included sync router

### The 3-Stage Filter Pipeline

**SRS Reference:** Section 2.2 - Transaction Discard/Ignore Policy

```python
# STAGE 1: Discard pending transactions
if txn.get('pending', False):
    continue

# STAGE 2: Only process credit card accounts
if account.type != 'credit' or account.subtype != 'credit card':
    continue

# STAGE 3: Mark non-analyzable transactions
is_analyzable = (
    amount > 0 and  # Not a refund
    primary_category not in {'LOAN_PAYMENTS', 'TRANSFER_IN', 'TRANSFER_OUT', 'LOAN_DISBURSEMENTS'}
)
```

**Stage 1: Pending Filter**
- **Why:** Pending transactions may have incorrect amounts (tips, adjustments)
- **Action:** Discard completely
- **Example:** Restaurant charge pending with $50, final settles at $60 with tip

**Stage 2: Account Type Filter**
- **Why:** We only optimize credit card rewards
- **Action:** Discard transactions from checking, savings, loans
- **Implementation:** Check account metadata, only process `type=='credit'` && `subtype=='credit card'`

**Stage 3: Analyzability Flag**
- **Why:** Some transactions don't earn rewards (payments, transfers, refunds)
- **Action:** Store but mark `is_analyzable=False`
- **Rationale:** Keep for ledger completeness, exclude from optimization

### UPSERT Logic

**SRS Reference:** FR 1.3 - Idempotent Upsert

```python
# Check if transaction exists by plaid_transaction_id (unique natural key)
existing_txn = session.exec(
    select(Transaction).where(Transaction.plaid_transaction_id == txn_id)
).first()

if existing_txn:
    # UPDATE: Plaid corrected the transaction
    for key, value in txn_data.items():
        setattr(existing_txn, key, value)
    transactions_updated += 1
else:
    # INSERT: New transaction
    new_txn = Transaction(**txn_data)
    session.add(new_txn)
    transactions_added += 1
```

**Why UPSERT is Critical:**
- Users can click "Refresh" multiple times
- Plaid may correct transaction data (merchant name, category, amount)
- Prevents duplicate transactions
- Maintains data integrity

**Natural Key:** `plaid_transaction_id` has a UNIQUE constraint in the database

### Cursor Management

**SRS Reference:** FR 1.2 - Cursor-Based Sync

```python
# 1. Get last cursor from PlaidItem
cursor = plaid_item.last_cursor  # May be None for first sync

# 2. Sync transactions using cursor
while has_more:
    response = plaid_client.transactions_sync(
        access_token=access_token,
        cursor=cursor
    )
    # Process transactions...
    cursor = response['next_cursor']
    has_more = response['has_more']

# 3. Save new cursor back to PlaidItem
plaid_item.last_cursor = cursor
plaid_item.updated_at = datetime.utcnow()
session.commit()
```

**Benefits:**
- Only fetch new/modified transactions (not all history)
- Efficient for regular syncs
- Handles Plaid's pagination automatically
- Supports unlimited transaction history

### Category Normalization Integration

Every transaction is automatically mapped to an internal bucket:

```python
from app.logic import get_mapper

mapper = get_mapper()
bucket = mapper.get_internal_bucket(primary_category, detailed_category)
```

This allows future optimization logic to know which reward rates apply.

### Automatic Card Creation

When syncing a new Plaid item, the endpoint automatically:

1. Fetches all credit card accounts for the item
2. Creates `Card` records if they don't exist
3. Maps `account_id` → `Card` for transaction association
4. Preserves existing cards (idempotent)

```python
for account_id, official_name in credit_accounts.items():
    card = session.exec(
        select(Card).where(Card.plaid_account_id == account_id)
    ).first()
    
    if not card:
        card = Card(
            plaid_item_id=plaid_item.id,
            plaid_account_id=account_id,
            official_name=official_name,
            reward_slug=None  # Set manually by user later
        )
        session.add(card)
```

### Response Format

```json
{
  "item_id": "uuid",
  "transactions_added": 15,
  "transactions_updated": 2,
  "transactions_removed": 0,
  "accounts_synced": 3,
  "cursor_updated": true
}
```

**Metrics Explained:**
- `transactions_added`: New transactions discovered
- `transactions_updated`: Existing transactions corrected by Plaid
- `transactions_removed`: Transactions deleted by Plaid (rare)
- `accounts_synced`: Number of credit card accounts processed
- `cursor_updated`: Whether new cursor was saved

### Environment Configuration

**Required in `.env`:**
```bash
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_secret_here
PLAID_ENV=sandbox  # or development, production
```

**Plaid Environments:**
- `sandbox`: Testing with fake data (development)
- `development`: Testing with real bank connections (limited)
- `production`: Live production data

### Key Design Decisions

**1. Cursor Storage in PlaidItem**
- **Decision:** Store `last_cursor` at the PlaidItem level
- **Rationale:** Each Plaid item has independent sync state
- **Benefit:** Multi-user support, independent sync schedules

**2. UPSERT on Transaction Level**
- **Decision:** Use `plaid_transaction_id` as natural key
- **Rationale:** Plaid corrects transactions, amounts may change
- **Benefit:** No duplicates, always have latest data

**3. Stage 3 Stores Non-Analyzable**
- **Decision:** Store refunds/payments but mark `is_analyzable=False`
- **Rationale:** Ledger completeness vs optimization scope
- **Benefit:** Full transaction history, clear audit trail

**4. Automatic Card Creation**
- **Decision:** Create cards automatically during sync
- **Rationale:** Reduces manual setup steps
- **Benefit:** User just needs to link bank, cards appear automatically

**5. Dependency Injection for Session**
- **Decision:** Use FastAPI's `Depends(get_session)`
- **Rationale:** Automatic session management, no manual commit/rollback
- **Benefit:** Clean code, prevents connection leaks

### Error Handling

**Plaid API Errors:**
```python
try:
    response = plaid_client.transactions_sync(request)
except plaid.ApiException as e:
    raise HTTPException(status_code=500, detail=f"Plaid API error: {str(e)}")
```

**Missing PlaidItem:**
```python
if not plaid_item:
    raise HTTPException(status_code=404, detail=f"PlaidItem {item_id} not found")
```

**No Credit Accounts:**
Returns success response with 0 transactions (not an error condition)

### Testing Strategy

**For MVP (with Sandbox):**
1. Create a PlaidItem with sandbox access_token
2. Call `POST /sync/{item_id}`
3. Verify transactions appear in database
4. Call sync again to test idempotency (no duplicates)
5. Verify cursor is updated in PlaidItem

**Future: Integration Tests**
- Mock Plaid API responses
- Test 3-stage filter with various transaction types
- Test UPSERT with modified transactions
- Test cursor pagination with large datasets

### Performance Considerations

**Current Implementation (MVP):**
- Sequential processing of transactions
- Single database commit after all processing
- No batch inserts (using individual UPSERTs)

**Future Optimizations:**
- [ ] Batch UPSERT with SQLAlchemy bulk operations
- [ ] Parallel processing of multiple items
- [ ] Background job queue for large syncs
- [ ] Caching of category mapper results

### Known Limitations (MVP)

1. **No Webhook Support:** Manual refresh only (SRS: out of scope for MVP)
2. **No Rate Limiting:** Could exceed Plaid API limits with frequent syncs
3. **Single-threaded:** One sync at a time per request
4. **No Partial Failure Handling:** All-or-nothing transaction commit
5. **No Sync Status Tracking:** Can't see "in progress" state

### Future Enhancements

- [ ] Add webhook endpoint for real-time transaction updates
- [ ] Implement background job queue (Celery/RQ) for async syncs
- [ ] Add sync status tracking (in_progress, completed, failed)
- [ ] Implement rate limiting and retry logic
- [ ] Add transaction deduplication by merchant + amount + date (beyond Plaid ID)
- [ ] Add user notification for sync completion
- [ ] Add manual transaction entry for non-Plaid accounts

---

### Issues Encountered During Acid Test

**Date:** 2026-01-04  
**Phase:** Acid Test Validation of Sync Engine

#### Issue 4: Missing Plaid Environment Variables in Docker

**Symptom:**
```
ValueError: PLAID_CLIENT_ID environment variable is required
```

**Root Cause:**  
The Plaid environment variables (`PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV`) were in `.env` file but not passed to the Docker container in `docker-compose.yml`.

**Solution:**
```yaml
# docker-compose.yml - backend service environment section
environment:
  # Existing vars...
  PLAID_CLIENT_ID: ${PLAID_CLIENT_ID}
  PLAID_SECRET: ${PLAID_SECRET}
  PLAID_ENV: ${PLAID_ENV}
```

**Key Learning:**
> ⚠️ **Docker Environment Variables:** Adding variables to `.env` is NOT enough. They must be explicitly mapped in `docker-compose.yml` to be accessible inside containers.

---

#### Issue 5: Plaid Sandbox Returns Only Checking Accounts

**Symptom:**
```
accounts_synced: 0
transactions_added: 0
```
Debug logs showed: `Account type=depository, subtype=checking`

**Investigation Process:**
1. Tried `user_transactions_dynamic` → Only checking accounts
2. Tried `user_yuppie` (persona) → Only checking accounts
3. Tried explicit account override → API error: `UNKNOWN_FIELDS`

**Root Cause:**  
Requesting only `initial_products: ["transactions"]` caused Plaid Sandbox to default to **checking accounts** with transaction history. Plaid Sandbox doesn't automatically provision credit card accounts unless explicitly signaled.

**Solution:**
Request BOTH products:
```bash
curl -X POST https://sandbox.plaid.com/sandbox/public_token/create \
  -d '{
    "client_id": "...",
    "secret": "...",
    "institution_id": "ins_109508",
    "initial_products": ["transactions", "liabilities"]  # ← BOTH required
  }'
```

**Why This Works:**
- `transactions` product → Provides detailed transaction history (merchant, amount, date)
- `liabilities` product → Signals to Plaid: "I need credit/loan accounts"
- Together → Plaid provisions **credit card accounts** WITH transaction history

**Key Learning:**
> 💡 **CRITICAL:** For credit card testing in Plaid Sandbox:
> - `["transactions"]` alone → Checking accounts with transactions
> - `["transactions", "liabilities"]` → Credit card accounts with transactions
> 
> The `liabilities` product doesn't just add metadata—it changes which account types are provisioned!

**Plaid Documentation Reference:**
- [Liabilities API](https://plaid.com/docs/api/products/liabilities/index.html.md): "Currently supported account types are account type `credit` with account subtype `credit card`"

---

#### Issue 6: Cursor Type Error on First Sync

**Symptom:**
```
plaid.exceptions.ApiTypeError: Invalid type for variable 'cursor'. 
Required value type is str and passed type was NoneType at ['cursor']
```

**Root Cause:**  
On first sync, `plaid_item.last_cursor` is `None`. The Plaid Python SDK doesn't accept `None` as a cursor value—it must either be omitted or be a string.

**Solution:**
```python
# Conditional request creation
if cursor:
    request = TransactionsSyncRequest(
        access_token=plaid_item.access_token,
        cursor=cursor
    )
else:
    request = TransactionsSyncRequest(
        access_token=plaid_item.access_token
        # Don't pass cursor parameter at all
    )
```

**Key Learning:**
> 💡 **Cursor Handling:** For first sync, omit the cursor parameter entirely rather than passing `None`. Plaid's API distinguishes between "no cursor" (fetch all) and "cursor=None" (invalid).

---

#### Issue 7: Date Type Mismatch

**Symptom:**
```python
TypeError: strptime() argument 1 must be str, not datetime.date
```

**Root Cause:**  
Plaid's Python SDK returns `date` fields as `datetime.date` objects (not strings), but the code assumed string format and tried to parse with `strptime()`.

**Solution:**
```python
# Handle both string and date object formats
txn_date = txn['date']
if isinstance(txn_date, str):
    txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
# else: already a date object, use as-is
```

**Key Learning:**
> 💡 **Plaid SDK Data Types:** The `plaid-python` SDK converts API responses to Python objects. Don't assume all fields are strings—check types when dealing with dates, decimals, etc.

---

#### Issue 8: Missing Email Validator Package

**Symptom:**
```
ImportError: email-validator is not installed, 
run `pip install 'pydantic[email]'`
```

**Root Cause:**  
Using Pydantic's `EmailStr` type requires the separate `email-validator` package, which wasn't in `requirements.txt`.

**Solution:**
```python
# requirements.txt
pydantic[email]>=2.7.0
email-validator>=2.1.0
```

**Key Learning:**
> 💡 **Pydantic Optional Dependencies:** Some Pydantic features require additional packages. Use the bracket notation `pydantic[email]` or install dependencies explicitly.

---

### Acid Test Results Summary

**Date:** 2026-01-04  
**Status:** ✅ PASSED (6/6 test categories)

**Data Synced:**
- 146 transactions imported
- 2 credit card accounts created automatically
- 1 PlaidItem connected
- 1 User created

**Credit Cards Created:**
1. Plaid Diamond 12.5% APR Interest Credit Card
2. Plaid Platinum Small Business Credit Card

**Test Category Results:**

✅ **Stage 1 & 2: Account Type Filter**
- All 146 transactions from credit cards (not checking) ✓
- No pending transactions stored ✓
- No wrong account types ✓

✅ **Stage 3: Analyzability Flag**
- 122 transactions (83.6%) marked `is_analyzable = true` ✓
- 24 transactions (16.4%) marked `is_analyzable = false` ✓
- Example verified: "AUTOMATIC PAYMENT - THANK" → `TRANSFER_OUT` → non-analyzable ✓

✅ **Plaid Category Normalization**
- All transactions have Plaid categories ✓
- Distribution: ENTERTAINMENT (25), TRAVEL (25), FOOD_AND_DRINK (24), etc. ✓
- Sample verified:
  - United Airlines → `TRAVEL` / `TRAVEL_FLIGHTS` ✓
  - KFC → `FOOD_AND_DRINK` / `FOOD_AND_DRINK_FAST_FOOD` ✓
  - Madison Bicycle Shop → `GENERAL_MERCHANDISE` / `SPORTING_GOODS` ✓

✅ **UPSERT Logic (Idempotency)**
- First sync: 146 transactions added ✓
- Second sync: 0 transactions added (no duplicates) ✓
- Database count: 146 (unchanged after second sync) ✓
- UPSERT on `plaid_transaction_id` working perfectly ✓

✅ **Data Integrity**
- All transactions have unique `plaid_transaction_id` ✓
- All amounts stored as `Decimal(12,2)` ✓
- All transactions have merchant names ✓
- All transactions have dates ✓
- Foreign key relationships maintained ✓

✅ **Cursor Management**
- `cursor_updated: true` after sync ✓
- `PlaidItem.last_cursor` saved in database ✓
- Future syncs will be incremental ✓

**Known Issue Discovered:**
⚠️ `internal_bucket` field is **missing from Transaction model**
- The sync code calls `mapper.get_internal_bucket()` and tries to set the field
- But the column doesn't exist in the database schema
- Plaid categories ARE being saved (can be mapped later)
- Fix needed: Add `internal_bucket` column to Transaction model

**Impact:** Medium priority
- Transactions sync successfully
- 3-stage filter working
- Plaid categories captured
- But optimization engine (Sub-Phase 1.5) will need `internal_bucket`

---

### Key Technical Insights from Acid Test

**1. Plaid Sandbox Credit Card Provisioning**

The `initial_products` array determines which account types are provisioned:

| Products Requested | Accounts Provisioned | Use Case |
|-------------------|---------------------|----------|
| `["transactions"]` | Checking accounts with transaction history | Bank account analysis |
| `["liabilities"]` | Credit cards without transactions | Debt metadata only |
| `["transactions", "liabilities"]` | **Credit cards WITH transactions** | GetCardIQ ✓ |

**Key Insight:**  
> The `liabilities` product isn't just for metadata—it's a **signal** to Plaid Sandbox about which account types to provision. Always include both for credit card transaction testing.

**2. UPSERT Performance**

With 146 transactions:
- First sync: ~4 seconds (all INSERTs)
- Second sync: ~1 second (all checks, 0 updates)
- No duplicates created despite multiple syncs

UPSERT strategy validated:
- Natural key (`plaid_transaction_id`) prevents duplicates ✓
- Sequential processing acceptable for MVP ✓
- Future: Batch operations could improve performance

**3. Category Distribution Analysis**

Real sandbox data showed balanced distribution:
- ENTERTAINMENT: 17.1%
- TRAVEL: 17.1%
- GENERAL_MERCHANDISE: 16.4%
- PERSONAL_CARE: 16.4%
- FOOD_AND_DRINK: 16.4%
- TRANSFER_OUT: 16.4%

This validates that:
- Plaid's sandbox data is realistic ✓
- Our 10-bucket system can handle diverse spending ✓
- GENERAL bucket usage is reasonable (transfers, payments)

**4. Analyzability Distribution**

83.6% analyzable vs 16.4% non-analyzable matches expectations:
- Most transactions are purchases (rewardable) ✓
- ~16% are payments/transfers (non-rewardable) ✓
- Matches typical credit card statement composition

---

#### Issue 9: Missing internal_bucket Field in Transaction Model

**Date:** 2026-01-07  
**Phase:** Post-Acid Test Schema Fix  
**Symptom:**
```
During acid test, discovered that internal_bucket values were calculated but not saved to database
```

**Root Cause:**  
The sync logic in `app/api/sync.py` was correctly calculating `internal_bucket` from the `NormalizationMapper`, but:
1. The `Transaction` model in `app/models/models.py` had no `internal_bucket` field
2. The `txn_data` dictionary was not including `internal_bucket`
3. Result: Category mapping worked perfectly, but values were never persisted

**Error Details:**
- Mapper calculated buckets correctly ✓
- 3-stage filter working ✓
- Transactions saved to database ✓
- But `internal_bucket` was silently ignored (column didn't exist)

**Solution (2-Part Fix):**

**1. Add Field to Transaction Model:**
```python
# app/models/models.py - After Plaid categories, before merchant_name

# Internal reward bucket mapping (from NormalizationMapper)
internal_bucket: Optional[str] = Field(
    default=None,
    sa_column=Column(String(50), index=True),
    description="Mapped reward bucket (DINING, GROCERY, GAS, etc.) from mapper"
)
```

**2. Add to txn_data Dictionary:**
```python
# app/api/sync.py - In the transaction processing loop

txn_data = {
    "card_id": card.id,
    "plaid_transaction_id": txn['transaction_id'],
    "amount": amount,
    "date": txn_date,
    "plaid_primary_category": primary_category,
    "plaid_detailed_category": detailed_category,
    "internal_bucket": internal_bucket.value,  # NEW: Add mapped bucket
    "merchant_name": txn.get('merchant_name') or txn.get('name'),
    "is_analyzable": is_analyzable,
    "updated_at": datetime.utcnow()
}
```

**3. Rebuild Database:**
```bash
docker-compose down -v  # Remove old volumes
docker-compose up -d --build  # Recreate schema with new field
```

**Verification:**
```bash
# Check schema
docker-compose exec -T db psql -U cashback_user -d cashback_db -c "\d transactions"

# Output shows:
# internal_bucket | character varying(50) | | | 
# Index: ix_transactions_internal_bucket btree (internal_bucket)
```

**Key Learning:**
> ⚠️ **Schema-First Development:** When adding new data to be persisted:
> 1. **FIRST:** Add field to SQLModel model
> 2. **THEN:** Rebuild database (or create migration)
> 3. **FINALLY:** Update logic to populate the field
> 
> Doing it in reverse order causes silent data loss!

**Why This Is Critical:**
- Without `internal_bucket`, the optimization engine (Sub-Phase 1.5) cannot function
- The field is indexed for fast queries: `WHERE internal_bucket = 'DINING'`
- Enables analytics: spending by category, bucket-level insights
- Required for reward calculation: match bucket to card's reward rules

**Impact:**
- **Before Fix:** Plaid categories saved, but not normalized buckets
- **After Fix:** Every transaction has its normalized reward bucket
- **Performance:** Index on `internal_bucket` enables fast aggregation queries

**Best Practices Established:**
1. Always add database fields BEFORE using them in logic
2. Use `docker-compose down -v` when schema changes
3. Verify schema after rebuild: `\d table_name`
4. Check SQLAlchemy logs for index creation
5. Test endpoints immediately after schema changes

---

## Best Practices Established

### 1. Relationship Definitions
**Decision:** For the MVP, we're **NOT** using SQLModel `Relationship()` objects to avoid circular reference issues.

**Rationale:**
- Foreign keys alone are sufficient for data integrity
- Relationships can be added later when needed for query optimization
- Prevents recursion issues during model initialization

**Implementation:**
```python
# Just use foreign keys
card_id: UUID = Field(foreign_key="cards.id", nullable=False, index=True)

# Don't add Relationship objects in MVP
# card: Card = Relationship(back_populates="transactions")  # Skip for now
```

### 2. Database Schema Verification
**Always verify tables after creation:**
```bash
# List all tables
docker-compose exec -T db psql -U cashback_user -d cashback_db -c "\dt"

# Check specific table schema
docker-compose exec -T db psql -U cashback_user -d cashback_db -c "\d transactions"
```

### 3. Type Imports Organization
```python
# Good pattern to avoid collisions
from datetime import datetime
from datetime import date as DateType
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import DECIMAL, String
```

---

## Debugging Commands

### Docker & Database
```bash
# Fresh start (removes volumes)
docker-compose down -v && docker-compose up --build -d

# Check logs
docker-compose logs backend --tail=50
docker-compose logs db --tail=50

# Restart backend only
docker-compose restart backend

# Access database directly
docker-compose exec db psql -U cashback_user -d cashback_db

# Check table schemas
docker-compose exec -T db psql -U cashback_user -d cashback_db -c "\d+ TABLE_NAME"
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/

# Database test
curl http://localhost:8000/db-test

# API documentation
open http://localhost:8000/docs
```

---

## Technical Decisions Log

### SQLModel Version Strategy
- **Decision:** Use `>=0.0.22` with Pydantic `>=2.7.0`
- **Rationale:** Older versions have known RecursionError issues with Pydantic v2
- **Date:** 2026-01-04

### UUID Primary Keys
- **Decision:** All primary keys use UUID (not auto-incrementing integers)
- **Rationale:** Better for distributed systems, prevents exposure of record counts
- **Implementation:** `uuid4()` for generation

### Decimal Precision
- **Decision:** Transaction amounts use `DECIMAL(12,2)`, cashback uses `DECIMAL(10,2)`
- **Rationale:** Financial data requires exact precision (not float)
- **SRS Reference:** Section 3.2

### Idempotency Strategy
- **Decision:** Use `plaid_transaction_id` as unique natural key
- **Implementation:** `UNIQUE` constraint + index
- **Rationale:** Allows UPSERT operations without creating duplicates
- **SRS Reference:** FR 1.3

---

## Resources & References

### Documentation
- [SQLModel Official Docs](https://sqlmodel.tiangolo.com/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pydantic Error Codes](https://errors.pydantic.dev/)

### Related Issues
- [SQLModel #445 - RecursionError with Pydantic v2](https://github.com/tiangolo/sqlmodel/issues/445)
- [Pydantic #6833 - Field name clashing](https://github.com/pydantic/pydantic/issues/6833)

---

## Future Considerations

### Items to Address in Later Phases
1. **Add Relationship objects** when implementing query-heavy features
2. **Implement connection pooling** for production
3. **Add database migrations** using Alembic
4. **Set up database backups** before production
5. **Add database indexes** for frequently queried fields beyond MVP

### Known Limitations (MVP)
- No bidirectional relationships (by design)
- No database migration system (manual schema changes)
- No connection pooling (single connection per request)
- No query result caching

---

**Last Updated:** 2026-01-07  
**Sub-Phase 1.4:** Complete with Acid Test Validation ✅  
**Schema Fix:** `internal_bucket` field added ✅  
**Next:** Re-run Acid Test to verify persistence → Sub-Phase 1.5

