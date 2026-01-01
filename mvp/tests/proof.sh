#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000/api/v1"
USER_ID="b40d1660-cdb3-4ed0-b0d3-2267b3d25072"

echo "🧪 PROOF OF CONCEPT: Cross-Session Memory"
echo "----------------------------------------"

# 1. Create Session A
echo "1. Creating Session A..."
SESS_A_RESP=$(curl -s -X POST "${BASE_URL}/chat/sessions?user_id=${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"title": "Session A"}')

SESS_A_ID=$(echo $SESS_A_RESP | jq -r '.id')
echo "✅ Session A: $SESS_A_ID"

# 2. Tell Name
echo "2. Telling Name in Session A..."
curl -s -X POST "${BASE_URL}/chat?user_id=${USER_ID}" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"My name is Ashish.\", \"session_id\": \"$SESS_A_ID\"}" | jq .message

echo "Waiting for vector ingestion..."
sleep 2

# 3. Create Session B
echo "3. Creating Session B (New Context)..."
SESS_B_RESP=$(curl -s -X POST "${BASE_URL}/chat/sessions?user_id=${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"title": "Session B"}')

SESS_B_ID=$(echo $SESS_B_RESP | jq -r '.id')
echo "✅ Session B: $SESS_B_ID"

# 4. Ask Name
echo "4. Asking Name in Session B..."
RESPONSE=$(curl -s -X POST "${BASE_URL}/chat?user_id=${USER_ID}" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is my name?\", \"session_id\": \"$SESS_B_ID\"}")

echo "📝 Response: $(echo $RESPONSE | jq .message)"
echo "🎯 Intent: $(echo $RESPONSE | jq .intent)"
