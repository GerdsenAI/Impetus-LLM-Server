#!/usr/bin/env bash
# test_server.sh - End-to-end test of Impetus LLM Server
# Usage: ./test_server.sh [model_id]
#
# This script:
#   1. Starts the server (if not already running)
#   2. Waits for health
#   3. Loads a model
#   4. Sends a test chat completion
#   5. Prints results
#
# API Key: The key is auto-generated on the first /v1/* request.
#   The script captures it from the server logs automatically.
#   To use a persistent key, set IMPETUS_API_KEY before running.

set -euo pipefail

MODEL_ID="${1:-Qwen3-4B-Instruct-2507-MLX-4bit}"
SERVER_URL="http://127.0.0.1:8080"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/tmp/impetus_test_server.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}ℹ${NC}  $*"; }
ok()    { echo -e "${GREEN}✅${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC}  $*"; }
fail()  { echo -e "${RED}❌${NC} $*"; exit 1; }

cleanup() {
    if [[ -n "${SERVER_PID:-}" ]]; then
        info "Stopping server (PID $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# --- Step 1: Check if server is already running ---
info "Checking if server is running on $SERVER_URL..."
if curl -sS --max-time 2 "$SERVER_URL/api/health" >/dev/null 2>&1; then
    ok "Server already running"
    SERVER_PID=""
else
    info "Starting server..."
    cd "$SCRIPT_DIR"

    if [[ ! -d ".venv" ]]; then
        fail "Virtual environment not found. Run: python3 -m venv .venv && pip install -r gerdsen_ai_server/requirements.txt"
    fi

    .venv/bin/python gerdsen_ai_server/src/main.py > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!

    # Wait for server to be ready (up to 30s)
    for i in $(seq 1 30); do
        if curl -sS --max-time 2 "$SERVER_URL/api/health" >/dev/null 2>&1; then
            ok "Server started (PID $SERVER_PID)"
            break
        fi
        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            echo ""
            fail "Server process exited. Check $LOG_FILE for errors."
        fi
        printf "."
        sleep 1
    done

    if ! curl -sS --max-time 2 "$SERVER_URL/api/health" >/dev/null 2>&1; then
        fail "Server failed to start within 30s. Check $LOG_FILE"
    fi
fi

# --- Step 2: Health check ---
info "Running health check..."
HEALTH=$(curl -sS "$SERVER_URL/api/health/status" 2>/dev/null || echo '{"error":"failed"}')
if echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='healthy' else 1)" 2>/dev/null; then
    ok "Health: healthy"
else
    warn "Health check returned: $HEALTH"
fi

# --- Step 3: Load model ---
info "Loading model: $MODEL_ID ..."
LOAD_RESULT=$(curl -sS -X POST "$SERVER_URL/api/models/load" \
    -H "Content-Type: application/json" \
    -d "{\"model_id\": \"$MODEL_ID\"}" 2>&1)

if echo "$LOAD_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status') in ('success','already_loaded') else 1)" 2>/dev/null; then
    STATUS=$(echo "$LOAD_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
    ok "Model loaded ($STATUS)"
else
    fail "Model load failed: $LOAD_RESULT"
fi

# --- Step 4: Trigger API key generation and capture it ---
info "Generating API key (first /v1 request)..."

# If user set IMPETUS_API_KEY, use that
if [[ -n "${IMPETUS_API_KEY:-}" ]]; then
    API_KEY="$IMPETUS_API_KEY"
    ok "Using IMPETUS_API_KEY from environment"
else
    # First request triggers key generation and succeeds without auth
    MODELS_RESULT=$(curl -sS "$SERVER_URL/v1/models" 2>&1)

    # Try to extract key from server logs
    sleep 1
    if [[ -f "$LOG_FILE" ]]; then
        API_KEY=$(grep -o 'impetus-[A-Za-z0-9_-]*' "$LOG_FILE" | head -1 || true)
    fi

    if [[ -z "${API_KEY:-}" ]]; then
        warn "Could not extract API key from logs. Check server console for the key."
        warn "Using placeholder - subsequent /v1/* requests may fail."
        API_KEY="placeholder"
    else
        ok "API key captured: ${API_KEY:0:20}..."
    fi
fi

# --- Step 5: Send test chat completion ---
info "Sending test chat completion..."
RESPONSE=$(curl -sS -X POST "$SERVER_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
        \"model\": \"$MODEL_ID\",
        \"messages\": [
            {\"role\": \"system\", \"content\": \"You are a helpful assistant. Be concise.\"},
            {\"role\": \"user\", \"content\": \"What is the capital of France? Answer in one sentence.\"}
        ],
        \"max_tokens\": 100,
        \"temperature\": 0.7,
        \"stream\": false
    }" 2>&1)

# Check response
if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'choices' in d else 1)" 2>/dev/null; then
    CONTENT=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])")
    TOKENS=$(echo "$RESPONSE" | python3 -c "import sys,json; u=json.load(sys.stdin)['usage']; print(f\"prompt={u['prompt_tokens']}, completion={u['completion_tokens']}, total={u['total_tokens']}\")")

    ok "Chat completion successful!"
    echo ""
    echo -e "  ${CYAN}Model:${NC}    $MODEL_ID"
    echo -e "  ${CYAN}Response:${NC} $CONTENT"
    echo -e "  ${CYAN}Tokens:${NC}  $TOKENS"
else
    fail "Chat completion failed: $RESPONSE"
fi

echo ""
echo -e "${GREEN}━━━ All tests passed! ━━━${NC}"
echo ""
echo -e "  ${CYAN}Server:${NC}  $SERVER_URL"
echo -e "  ${CYAN}API Key:${NC} ${API_KEY:0:30}..."
echo -e "  ${CYAN}Model:${NC}   $MODEL_ID"
echo ""
echo "To send your own code for review:"
echo "  curl -X POST $SERVER_URL/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer $API_KEY' \\"
echo "    -d '{\"model\":\"$MODEL_ID\",\"messages\":[{\"role\":\"user\",\"content\":\"Review this...\"}]}'"
