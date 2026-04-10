#!/bin/bash
# Populates TaskFlow with sample data for manual API testing.
# Usage: ./scripts/populate.sh [BASE_URL]

BASE="${1:-http://localhost:8000}"
CT="Content-Type: application/json"

echo "=== TaskFlow Data Population ==="
echo "Target: $BASE"
echo ""

# ── Register users ──────────────────────────────────────────────

echo "--- Registering users ---"

ALICE=$(curl -s -X POST "$BASE/auth/register" -H "$CT" -d '{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "password": "alice123"
}')
ALICE_TOKEN=$(echo "$ALICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
ALICE_ID=$(echo "$ALICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
echo "Alice: id=$ALICE_ID"

BOB=$(curl -s -X POST "$BASE/auth/register" -H "$CT" -d '{
  "name": "Bob Smith",
  "email": "bob@example.com",
  "password": "bob12345"
}')
BOB_TOKEN=$(echo "$BOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
BOB_ID=$(echo "$BOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
echo "Bob:   id=$BOB_ID"

CHARLIE=$(curl -s -X POST "$BASE/auth/register" -H "$CT" -d '{
  "name": "Charlie Dev",
  "email": "charlie@example.com",
  "password": "charlie1"
}')
CHARLIE_TOKEN=$(echo "$CHARLIE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
CHARLIE_ID=$(echo "$CHARLIE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
echo "Charlie: id=$CHARLIE_ID"

# Also login as the seed user
SEED=$(curl -s -X POST "$BASE/auth/login" -H "$CT" -d '{
  "email": "test@example.com",
  "password": "password123"
}')
SEED_TOKEN=$(echo "$SEED" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
SEED_ID=$(echo "$SEED" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
echo "Test User (seed): id=$SEED_ID"

echo ""

# ── Create projects ─────────────────────────────────────────────

echo "--- Creating projects ---"

P1=$(curl -s -X POST "$BASE/projects" -H "$CT" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d '{"name": "Mobile App", "description": "iOS and Android app for Q3 launch"}')
P1_ID=$(echo "$P1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "Mobile App (Alice): id=$P1_ID"

P2=$(curl -s -X POST "$BASE/projects" -H "$CT" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -d '{"name": "API Refactor", "description": "Break monolith into microservices"}')
P2_ID=$(echo "$P2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "API Refactor (Bob): id=$P2_ID"

P3=$(curl -s -X POST "$BASE/projects" -H "$CT" \
  -H "Authorization: Bearer $CHARLIE_TOKEN" \
  -d '{"name": "Design System", "description": "Shared component library"}')
P3_ID=$(echo "$P3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "Design System (Charlie): id=$P3_ID"

echo ""

# ── Create tasks ────────────────────────────────────────────────

echo "--- Creating tasks ---"

# Mobile App tasks (Alice's project, mix of assignees)
curl -s -X POST "$BASE/projects/$P1_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d "{\"title\": \"Set up React Native project\", \"description\": \"Initialize repo with Expo\", \"priority\": \"high\", \"assignee_id\": \"$ALICE_ID\", \"due_date\": \"2026-04-20\"}" > /dev/null
echo "  [Mobile App] Set up React Native project (high, Alice)"

curl -s -X POST "$BASE/projects/$P1_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d "{\"title\": \"Design login screen\", \"priority\": \"high\", \"assignee_id\": \"$BOB_ID\", \"due_date\": \"2026-04-22\"}" > /dev/null
echo "  [Mobile App] Design login screen (high, Bob)"

curl -s -X POST "$BASE/projects/$P1_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d "{\"title\": \"Push notification setup\", \"description\": \"Firebase integration\", \"priority\": \"medium\", \"due_date\": \"2026-05-01\"}" > /dev/null
echo "  [Mobile App] Push notification setup (medium, unassigned)"

curl -s -X POST "$BASE/projects/$P1_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -d "{\"title\": \"Write unit tests for auth\", \"priority\": \"low\", \"assignee_id\": \"$CHARLIE_ID\"}" > /dev/null
echo "  [Mobile App] Write unit tests for auth (low, Charlie)"

# API Refactor tasks (Bob's project)
curl -s -X POST "$BASE/projects/$P2_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -d "{\"title\": \"Extract user service\", \"description\": \"Move user logic to its own service\", \"priority\": \"high\", \"assignee_id\": \"$BOB_ID\", \"due_date\": \"2026-04-18\"}" > /dev/null
echo "  [API Refactor] Extract user service (high, Bob)"

curl -s -X POST "$BASE/projects/$P2_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -d "{\"title\": \"Set up service mesh\", \"priority\": \"medium\", \"assignee_id\": \"$ALICE_ID\", \"due_date\": \"2026-04-25\"}" > /dev/null
echo "  [API Refactor] Set up service mesh (medium, Alice)"

curl -s -X POST "$BASE/projects/$P2_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -d '{"title": "Update API docs", "priority": "low"}' > /dev/null
echo "  [API Refactor] Update API docs (low, unassigned)"

# Design System tasks (Charlie's project)
curl -s -X POST "$BASE/projects/$P3_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $CHARLIE_TOKEN" \
  -d "{\"title\": \"Create button component\", \"priority\": \"high\", \"assignee_id\": \"$CHARLIE_ID\", \"due_date\": \"2026-04-15\"}" > /dev/null
echo "  [Design System] Create button component (high, Charlie)"

curl -s -X POST "$BASE/projects/$P3_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $CHARLIE_TOKEN" \
  -d "{\"title\": \"Build form inputs\", \"description\": \"Text, select, checkbox, radio\", \"priority\": \"high\", \"assignee_id\": \"$ALICE_ID\", \"due_date\": \"2026-04-19\"}" > /dev/null
echo "  [Design System] Build form inputs (high, Alice)"

curl -s -X POST "$BASE/projects/$P3_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $CHARLIE_TOKEN" \
  -d "{\"title\": \"Write Storybook stories\", \"priority\": \"medium\", \"assignee_id\": \"$BOB_ID\"}" > /dev/null
echo "  [Design System] Write Storybook stories (medium, Bob)"

curl -s -X POST "$BASE/projects/$P3_ID/tasks" -H "$CT" \
  -H "Authorization: Bearer $CHARLIE_TOKEN" \
  -d '{"title": "Accessibility audit", "priority": "medium"}' > /dev/null
echo "  [Design System] Accessibility audit (medium, unassigned)"

echo ""
echo "=== Done ==="
echo ""
echo "Credentials for manual testing:"
echo "  test@example.com / password123  (seed user)"
echo "  alice@example.com / alice123"
echo "  bob@example.com / bob12345"
echo "  charlie@example.com / charlie1"
echo ""
echo "Projects created: Mobile App, API Refactor, Design System"
echo "Tasks created: 11 (across 3 projects, various priorities & assignees)"
