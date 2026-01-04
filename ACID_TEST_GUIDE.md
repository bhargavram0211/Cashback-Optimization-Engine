# Acid Test Guide: Sub-Phase 1.4 - Sync Engine

## ✅ What We've Built

### New API Endpoints

We've added proper API endpoints for testing (no more manual SQL needed!):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /users` | POST | Create a new user |
| `GET /users` | GET | List all users |
| `GET /users/{user_id}` | GET | Get a specific user |
| `POST /items` | POST | Create a new PlaidItem |
| `GET /items` | GET | List all PlaidItems |
| `GET /items/{item_id}` | GET | Get a specific PlaidItem |
| `POST /sync/{item_id}` | POST | Sync transactions from Plaid |

### What We've Validated So Far

✅ **Backend Health**: Running and accessible  
✅ **Database Connection**: Connected to PostgreSQL  
✅ **User Creation API**: Successfully creates users  
✅ **PlaidItem Creation API**: Successfully creates items  
✅ **Plaid Client Initialization**: Credentials loaded correctly  
✅ **Sync Endpoint**: Makes API calls to Plaid

## 🧪 The Complete Acid Test

### Step 1: Create a User (via API)

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "created_at": "2026-01-04T12:00:00"
}
```

**Copy the `id`** - you'll need it for Step 2.

---

### Step 2: Get a Real Plaid Sandbox Access Token

The Plaid sandbox requires a **real** access token generated through Plaid Link.

#### Option A: Use Plaid Quickstart (Recommended)

1. **Run Plaid Quickstart:**
   ```bash
   # Set your Plaid credentials first
   export PLAID_CLIENT_ID=your_client_id
   export PLAID_SECRET=your_secret
   
   # Run the quickstart
   docker run --rm -p 3000:3000 \
     -e PLAID_CLIENT_ID=$PLAID_CLIENT_ID \
     -e PLAID_SECRET=$PLAID_SECRET \
     -e PLAID_ENV=sandbox \
     plaid/quickstart /bin/bash -c "cd /quickstart/node && node index.js"
   ```

2. **Open the UI:**
   ```
   http://localhost:3000
   ```

3. **Complete the Link flow:**
   - Click "Link Account"
   - Select any bank (First Platypus Bank recommended)
   - Use sandbox credentials:
     - Username: `user_good`
     - Password: `pass_good`

4. **Copy the access_token** from the terminal output.

#### Option B: Use Plaid's Test Access Token

For quick testing, you can also use Plaid's public sandbox token format. However, this will only work if you've registered your credentials with Plaid first.

---

### Step 3: Create a PlaidItem (via API)

Use the user ID from Step 1 and the access_token from Step 2:

```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID_FROM_STEP_1",
    "access_token": "YOUR_REAL_ACCESS_TOKEN_FROM_STEP_2",
    "institution_id": "ins_3"
  }'
```

**Expected Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "institution_id": "ins_3",
  "last_cursor": null,
  "created_at": "2026-01-04T12:00:00",
  "updated_at": "2026-01-04T12:00:00"
}
```

**Copy the `id`** - you'll need it for Step 4.

---

### Step 4: Sync Transactions (The Big Test!)

Trigger the sync endpoint:

```bash
curl -X POST http://localhost:8000/sync/YOUR_ITEM_ID_FROM_STEP_3
```

**Expected Response (Success):**
```json
{
  "item_id": "660e8400-e29b-41d4-a716-446655440000",
  "transactions_added": 15,
  "transactions_updated": 0,
  "transactions_removed": 0,
  "accounts_synced": 3,
  "cursor_updated": true
}
```

**What to Look For:**
- `transactions_added` > 0 (historical transactions fetched)
- `accounts_synced` > 0 (credit card accounts found)
- `cursor_updated` = true (cursor saved for next sync)

---

### Step 5: Verify the 3-Stage Filter (Database Audit)

Connect to the database and inspect the results:

```bash
docker exec cashback_db psql -U cashback_user -d cashback_db \
  -x -c "SELECT merchant_name, amount, internal_bucket, is_analyzable FROM transactions LIMIT 5;"
```

**Success Criteria:**

✅ **Stage 1 & 2 (Account Type Filter):**
- All transactions should be from credit card accounts
- No pending transactions stored

✅ **Stage 3 (Analyzability Flag):**
- Look for a "Payment" or "Transfer" transaction
- Should have `is_analyzable = f` (false)
- Regular purchase transactions should have `is_analyzable = t` (true)

✅ **Category Normalization:**
- All transactions should have an `internal_bucket` value
- Should see buckets like `DINING`, `TRAVEL`, `GROCERY`, `GAS`, etc.
- NO transactions should have `NULL` or empty bucket

**Example Expected Output:**
```
merchant_name   | Starbucks
amount          | 5.75
internal_bucket | DINING
is_analyzable   | t

merchant_name   | Shell Gas Station
amount          | 45.00
internal_bucket | GAS
is_analyzable   | t

merchant_name   | Credit Card Payment
amount          | -500.00
internal_bucket | GENERAL
is_analyzable   | f
```

---

### Step 6: Test Idempotency (UPSERT Logic)

Run the sync **again** with the same item_id:

```bash
curl -X POST http://localhost:8000/sync/YOUR_ITEM_ID_FROM_STEP_3
```

**Expected Response (Idempotent):**
```json
{
  "item_id": "660e8400-e29b-41d4-a716-446655440000",
  "transactions_added": 0,  👈 Should be ZERO!
  "transactions_updated": 0,
  "transactions_removed": 0,
  "accounts_synced": 3,
  "cursor_updated": true
}
```

**Success Criteria:**
- `transactions_added` = 0 (no duplicates created)
- Database transaction count should NOT increase

**Verify in Database:**
```bash
docker exec cashback_db psql -U cashback_user -d cashback_db \
  -c "SELECT COUNT(*) FROM transactions;"
```

The count should be **the same** as before the second sync.

---

### Step 7: Verify Cursor Management

Check that the cursor was saved:

```bash
curl http://localhost:8000/items/YOUR_ITEM_ID_FROM_STEP_3 | python3 -m json.tool
```

**Expected Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "institution_id": "ins_3",
  "last_cursor": "abc123xyz456...",  👈 Should NOT be null!
  "created_at": "2026-01-04T12:00:00",
  "updated_at": "2026-01-04T12:05:00"  👈 Should be updated
}
```

**Success Criteria:**
- `last_cursor` is NOT null
- `last_cursor` has a value (usually a long encoded string)
- `updated_at` timestamp is more recent than `created_at`

---

### Step 8: Verify Automatic Card Creation

Check that credit card accounts were created:

```bash
docker exec cashback_db psql -U cashback_user -d cashback_db \
  -c "SELECT id, official_name, reward_slug FROM cards WHERE plaid_item_id = 'YOUR_ITEM_ID_FROM_STEP_3';"
```

**Expected Output:**
```
                  id                  |    official_name     | reward_slug 
--------------------------------------+----------------------+-------------
 770e8400-e29b-41d4-a716-446655440000 | Plaid Credit Card    | 
 880e8400-e29b-41d4-a716-446655440000 | Plaid Saving         | 
(2 rows)
```

**Success Criteria:**
- At least 1 card created
- `official_name` matches Plaid's account names
- `reward_slug` is NULL (to be set by user later)

---

### Step 9: Verify Category Distribution

Get a breakdown of how transactions were categorized:

```bash
docker exec cashback_db psql -U cashback_user -d cashback_db \
  -c "SELECT internal_bucket, COUNT(*) as count FROM transactions GROUP BY internal_bucket ORDER BY count DESC;"
```

**Expected Output:**
```
 internal_bucket | count 
-----------------+-------
 GENERAL         |    45
 DINING          |    12
 GAS             |     8
 GROCERY         |     7
 TRAVEL          |     3
 ONLINE_SHOPPING |     2
(6 rows)
```

**Success Criteria:**
- Multiple buckets represented (not all GENERAL)
- Categories make sense for sandbox data
- Total count matches transaction count

---

## 🎉 Success Markers

If all steps pass, you've validated:

✅ **Infrastructure**: Backend, database, Docker all working  
✅ **API Design**: RESTful endpoints for users and items  
✅ **Plaid Integration**: Client initialization, API calls  
✅ **3-Stage Filter**: Pending, account type, analyzability  
✅ **Category Normalization**: PFCv2 → internal buckets  
✅ **UPSERT Logic**: No duplicates, idempotent syncs  
✅ **Cursor Management**: Incremental sync support  
✅ **Automatic Card Creation**: Cards created from accounts  
✅ **Data Integrity**: Decimal amounts, unique constraints  

---

## 🐛 Troubleshooting

### "INVALID_ACCESS_TOKEN" Error

**Problem:** Plaid says the access token is invalid.

**Solution:**
- You're using a made-up token instead of a real one
- Follow Step 2 to get a real Plaid Sandbox access token
- Make sure your `PLAID_CLIENT_ID` and `PLAID_SECRET` are correct

---

### "No transactions synced" (transactions_added = 0 on first sync)

**Problem:** First sync returned 0 transactions.

**Possible Causes:**
1. **No credit card accounts:** Plaid item only has checking/savings
   - Solution: Use a different sandbox item with credit cards
2. **All transactions filtered out:** Only payments/transfers present
   - Solution: Normal behavior, those are marked non-analyzable

---

### "Plaid API error: Rate limit exceeded"

**Problem:** Too many API calls in sandbox.

**Solution:**
- Wait a few minutes before retrying
- Sandbox has stricter rate limits than production
- Consider using development environment for heavy testing

---

### Database connection failed

**Problem:** Backend can't reach PostgreSQL.

**Solution:**
```bash
# Restart the entire stack
docker-compose down && docker-compose up -d

# Wait for health check
docker-compose logs db | grep "database system is ready"
```

---

## 📊 Viewing the Results

**Interactive API Docs:**
```
http://localhost:8000/docs
```

**Alternative Docs:**
```
http://localhost:8000/redoc
```

**Database CLI:**
```bash
docker exec -it cashback_db psql -U cashback_user -d cashback_db
```

Useful queries:
```sql
-- See all transactions
SELECT merchant_name, amount, internal_bucket, is_analyzable FROM transactions;

-- Bucket distribution
SELECT internal_bucket, COUNT(*) FROM transactions GROUP BY internal_bucket;

-- Analyzable vs non-analyzable
SELECT is_analyzable, COUNT(*) FROM transactions GROUP BY is_analyzable;

-- See cursor status
SELECT id, institution_id, last_cursor FROM plaid_items;
```

---

## 🚀 What's Next?

With a working sync engine, you're ready for:

- **Sub-Phase 1.5:** Optimization Engine
  - Calculate `best_card_id` for each transaction
  - Compute `lost_savings` (opportunity cost)
  - Build recommendation logic

- **Frontend Integration:**
  - Implement Plaid Link UI
  - Display transaction history
  - Show optimization insights

- **Reward Rules:**
  - Define card reward profiles
  - Map cards to reward structures
  - Calculate actual vs optimal cashback

---

## 📝 Notes

- This guide assumes you're using **Plaid Sandbox** environment
- For **development** or **production** environments, you'll need:
  - Real bank connections
  - Webhooks for real-time updates
  - More robust error handling
  - Rate limiting and retry logic

- The `/users` and `/items` endpoints are for **testing/development only**
- In production, these would require:
  - Authentication (JWT tokens)
  - Authorization (user owns the item)
  - Input validation and sanitization
  - Audit logging

---

**Last Updated:** 2026-01-04  
**Version:** Sub-Phase 1.4 Complete

