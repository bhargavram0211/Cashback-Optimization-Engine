#!/bin/bash

# Acid Test for Sub-Phase 1.4: Sync Engine
# This script performs comprehensive end-to-end testing using bash and curl

set -e

BACKEND_URL="http://localhost:8000"
SANDBOX_TOKEN="access-sandbox-8ab976e6-64bc-4b38-98f7-731e7a349970"
TEST_EMAIL="acid_test@example.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_RUN=0
TESTS_PASSED=0

print_header() {
    echo ""
    echo "================================================================================"
    echo "  $1"
    echo "================================================================================"
}

print_section() {
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────────"
    echo "  $1"
    echo "────────────────────────────────────────────────────────────────────────────────"
}

print_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    if [ "$1" = "PASS" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✅ PASS${NC} | $2"
    else
        echo -e "${RED}❌ FAIL${NC} | $2"
    fi
    if [ ! -z "$3" ]; then
        echo "      └─ $3"
    fi
}

print_header "ACID TEST: SUB-PHASE 1.4 - SYNC ENGINE"

# Test 1: Backend Health
print_section "TEST 1: Backend Health Check"
RESPONSE=$(curl -s -w "\n%{http_code}" $BACKEND_URL/ || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_test "PASS" "Backend health check" "Status: Backend is Online"
else
    print_test "FAIL" "Backend health check" "HTTP $HTTP_CODE - Backend is not running"
    echo ""
    echo "❌ Backend is not running. Start with: docker-compose up"
    exit 1
fi

# Test 2: Database Connection
print_section "TEST 2: Database Connection"
RESPONSE=$(curl -s -w "\n%{http_code}" $BACKEND_URL/db-test || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "Database Connected"; then
    print_test "PASS" "Database connection" "Status: Database Connected"
else
    print_test "FAIL" "Database connection" "Failed to connect to database"
    exit 1
fi

# Test 3 & 4: Create test data using Python (no external deps needed)
print_section "TEST 3 & 4: Create Test User and PlaidItem"
echo "Creating test user and PlaidItem in database..."

SETUP_SCRIPT=$(cat <<'EOF'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, select
from app.models.models import User, PlaidItem
from app.core.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    # Get or create user
    user = session.exec(
        select(User).where(User.email == "acid_test@example.com")
    ).first()
    
    if not user:
        user = User(email="acid_test@example.com", full_name="Acid Test User")
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # Get or create PlaidItem
    item = session.exec(
        select(PlaidItem).where(PlaidItem.access_token == "access-sandbox-8ab976e6-64bc-4b38-98f7-731e7a349970")
    ).first()
    
    if not item:
        item = PlaidItem(
            user_id=user.id,
            access_token="access-sandbox-8ab976e6-64bc-4b38-98f7-731e7a349970",
            institution_name="Sandbox Bank",
            last_cursor=None
        )
        session.add(item)
        session.commit()
        session.refresh(item)
    
    print(f"{user.id}|{item.id}")
EOF
)

RESULT=$(python3 -c "$SETUP_SCRIPT" 2>&1)
if [ $? -eq 0 ]; then
    USER_ID=$(echo "$RESULT" | cut -d'|' -f1)
    ITEM_ID=$(echo "$RESULT" | cut -d'|' -f2)
    print_test "PASS" "Test user creation" "User ID: $USER_ID"
    print_test "PASS" "PlaidItem creation" "Item ID: $ITEM_ID"
else
    print_test "FAIL" "Test data setup" "Error: $RESULT"
    exit 1
fi

# Test 5: First Sync (Historical)
print_section "TEST 5: First Sync (Historical)"
echo "Syncing transactions from Plaid Sandbox (this may take 10-30 seconds)..."

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/sync/$ITEM_ID" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    TXN_ADDED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transactions_added', 0))" 2>/dev/null || echo "0")
    TXN_UPDATED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transactions_updated', 0))" 2>/dev/null || echo "0")
    ACCOUNTS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('accounts_synced', 0))" 2>/dev/null || echo "0")
    
    if [ "$TXN_ADDED" -gt "0" ] && [ "$ACCOUNTS" -gt "0" ]; then
        print_test "PASS" "First sync" "Added: $TXN_ADDED, Updated: $TXN_UPDATED, Accounts: $ACCOUNTS"
    else
        print_test "FAIL" "First sync" "No transactions added (Added: $TXN_ADDED, Accounts: $ACCOUNTS)"
    fi
else
    print_test "FAIL" "First sync" "HTTP $HTTP_CODE: $(echo $BODY | head -c 100)"
fi

# Test 6: Idempotent Sync
print_section "TEST 6: Idempotent Sync (No Duplicates)"
echo "Running sync again to test idempotency..."

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/sync/$ITEM_ID" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    TXN_ADDED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transactions_added', 0))" 2>/dev/null || echo "0")
    TXN_UPDATED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transactions_updated', 0))" 2>/dev/null || echo "0")
    
    if [ "$TXN_ADDED" -eq "0" ]; then
        print_test "PASS" "Idempotent sync" "Added: $TXN_ADDED (expected 0), Updated: $TXN_UPDATED"
    else
        print_test "FAIL" "Idempotent sync" "Added: $TXN_ADDED (expected 0) - Duplicates created!"
    fi
else
    print_test "FAIL" "Idempotent sync" "HTTP $HTTP_CODE"
fi

# Tests 7-11: Database verification using Python
print_section "TESTS 7-11: Database Verification"

VERIFY_SCRIPT=$(cat <<EOF
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, select
from app.models.models import PlaidItem, Card, Transaction
from app.core.database import DATABASE_URL
from decimal import Decimal

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    # Test 7: Cursor Management
    item = session.get(PlaidItem, "$ITEM_ID")
    cursor_ok = item and item.last_cursor and len(item.last_cursor) > 0
    print(f"CURSOR|{'PASS' if cursor_ok else 'FAIL'}|{item.last_cursor[:30] if cursor_ok else 'None'}...")
    
    # Test 8: Automatic Card Creation
    cards = session.exec(select(Card).where(Card.plaid_item_id == "$ITEM_ID")).all()
    cards_ok = len(cards) > 0
    print(f"CARDS|{'PASS' if cards_ok else 'FAIL'}|{len(cards)} cards created")
    
    if cards_ok:
        card_ids = [card.id for card in cards]
        
        # Test 9: Transaction Storage
        txns = session.exec(select(Transaction).where(Transaction.card_id.in_(card_ids))).all()
        txns_ok = len(txns) > 0
        print(f"TXN_STORAGE|{'PASS' if txns_ok else 'FAIL'}|{len(txns)} transactions stored")
        
        if txns_ok:
            # Test 10: Data Integrity
            required_ok = all(t.plaid_transaction_id and t.merchant_name and t.amount is not None for t in txns)
            unique_ok = len(set(t.plaid_transaction_id for t in txns)) == len(txns)
            decimal_ok = all(isinstance(t.amount, Decimal) for t in txns)
            bucket_ok = all(t.internal_bucket for t in txns)
            
            integrity_ok = required_ok and unique_ok and decimal_ok and bucket_ok
            print(f"DATA_INTEGRITY|{'PASS' if integrity_ok else 'FAIL'}|Required: {required_ok}, Unique: {unique_ok}, Decimal: {decimal_ok}, Bucket: {bucket_ok}")
            
            # Test 11: 3-Stage Filter & Category Normalization
            analyzable = [t for t in txns if t.is_analyzable]
            non_analyzable = [t for t in txns if not t.is_analyzable]
            
            bucket_counts = {}
            for t in txns:
                bucket = t.internal_bucket or "NONE"
                bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
            
            filter_ok = "NONE" not in bucket_counts
            print(f"FILTER_CATEGORY|{'PASS' if filter_ok else 'FAIL'}|Analyzable: {len(analyzable)}, Non-analyzable: {len(non_analyzable)}, Buckets: {len(bucket_counts)}")
            
            # Print bucket distribution
            print("BUCKETS|" + "|".join(f"{k}:{v}" for k, v in sorted(bucket_counts.items(), key=lambda x: -x[1])))
    else:
        print("TXN_STORAGE|FAIL|No cards to check")
        print("DATA_INTEGRITY|FAIL|No transactions to check")
        print("FILTER_CATEGORY|FAIL|No transactions to check")
EOF
)

VERIFY_RESULT=$(python3 -c "$VERIFY_SCRIPT" 2>&1)

while IFS='|' read -r test status details; do
    case $test in
        CURSOR)
            print_test "$status" "Cursor management" "Cursor: $details"
            ;;
        CARDS)
            print_test "$status" "Automatic card creation" "$details"
            ;;
        TXN_STORAGE)
            print_test "$status" "Transaction storage" "$details"
            ;;
        DATA_INTEGRITY)
            print_test "$status" "Data integrity" "$details"
            ;;
        FILTER_CATEGORY)
            print_test "$status" "3-stage filter & category normalization" "$details"
            ;;
        BUCKETS)
            echo ""
            echo "      Bucket Distribution:"
            IFS='|' read -ra BUCKETS <<< "$details"
            for bucket in "${BUCKETS[@]}"; do
                echo "      • $bucket"
            done
            ;;
    esac
done <<< "$VERIFY_RESULT"

# Final Summary
print_header "FINAL RESULTS"
echo ""
echo "Score: $TESTS_PASSED/$TESTS_RUN tests passed ($(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED/$TESTS_RUN)*100}")%)"
echo ""

if [ "$TESTS_PASSED" -eq "$TESTS_RUN" ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Sub-Phase 1.4 is fully functional!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the output above for details.${NC}"
fi

print_header "ACID TEST COMPLETE"

