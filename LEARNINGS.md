# Project Learnings & Troubleshooting Guide

This document captures issues encountered during development, their root causes, and solutions. It serves as a knowledge base for future development and debugging.

---

## Table of Contents
- [Sub-Phase 1.1: Infrastructure Shell](#sub-phase-11-infrastructure-shell)
- [Sub-Phase 1.2: Data Models](#sub-phase-12-data-models)
- [Sub-Phase 1.3: Category Mapper](#sub-phase-13-category-mapper)

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

**Future Enhancements:**
- [ ] Add CSV-based configuration for easier updates
- [ ] Add merchant name overrides (e.g., "Costco" → WHOLESALE even if categorized as GROCERY)
- [ ] Add confidence scores for ambiguous mappings
- [ ] Add analytics endpoint to show mapping distribution across actual transactions
- [ ] Refine primary fallbacks based on audit results
- [ ] Create TRANSPORTATION bucket separate from GAS?

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

**Last Updated:** 2026-01-04  
**Next Update:** After Sub-Phase 1.4 completion

