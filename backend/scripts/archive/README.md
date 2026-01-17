# Archived Scripts

This folder contains scripts that are no longer used but preserved for historical reference.

## seed_poc_cards.py.OBSOLETE

**Status:** OBSOLETE - Do not use  
**Archived:** January 16, 2026  
**Reason:** Replaced by `seed_card_products.py` in Sprint 1

### Why This Script Was Replaced

This script was part of the POC/testing phase and included a "manipulation" step that artificially forced all transactions to use a single card (Zolve US). This was useful for testing but created a "Reality Gap" - the optimizer was calculating results based on fake card assignments, not real Plaid data.

**What it did (BAD):**
```python
# The Manipulation Step
for txn in transactions:
    txn.card_id = zolve_card_id  # Force all transactions to use Zolve
```

This defeated the purpose of the optimizer because:
- Plaid sync would set the correct card_id based on real usage
- Then this script would overwrite it with fake data
- The optimizer would calculate "lost savings" based on the manipulation, not reality

### Sprint 1 Solution

Sprint 1 introduced a new architecture:
- **CardProduct** - Master library of card types (shared by all users)
- **UserCard** - User-specific card instances (one per Plaid account)
- **Identification Flow** - Users identify which CardProduct their UserCard represents

**New script:** `seed_card_products.py`
- Seeds the CardProduct master library (10 cards)
- Does NOT create UserCards (Plaid sync does that)
- Does NOT manipulate transactions
- No more Reality Gap!

### Migration Notes

If you have old data from this script:
1. Run `docker-compose down -v` to wipe the database
2. Run `seed_card_products.py` to create the CardProduct library
3. Run Plaid sync to create UserCards
4. Use the frontend "Identify My Cards" page to link them

### Historical Reference

This script is preserved for:
- Understanding the evolution of the codebase
- Reference for the old Card model structure
- Demonstrating the problem that Sprint 1 solved

**Do not run this script!** It will cause conflicts with the new architecture.

---

**Last Modified:** Phase 3.2 (January 11, 2026)  
**Archived:** Sprint 1 (January 16, 2026)  
**Replacement:** `seed_card_products.py`
