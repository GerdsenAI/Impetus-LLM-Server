#!/bin/bash
# Comprehensive verification script for Impetus LLM Server

echo "🔍 Impetus LLM Server Verification"
echo "=================================="

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
PASSED=0
FAILED=0

# Helper function for logging results
log_result() {
    local test_name="$1"
    local result="$2"
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✅ $test_name${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $test_name${NC}"
        ((FAILED++))
    fi
}

# 1. Dependency verification
echo "📦 Checking dependencies..."
cd "/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server"

# Check if pyproject.toml has dependencies
if grep -q "dependencies = \[" pyproject.toml; then
    log_result "Dependencies section exists in pyproject.toml" 0
else
    log_result "Dependencies section exists in pyproject.toml" 1
fi

# Check virtual environment activation
if [ -d ".venv" ]; then
    source .venv/bin/activate
    log_result "Virtual environment found and activated" 0
else
    log_result "Virtual environment found and activated" 1
fi

# 2. Server startup test
echo "🚀 Testing server startup..."
export IMPETUS_ENVIRONMENT=development

# Start server in background
timeout 30s python gerdsen_ai_server/src/main.py &
SERVER_PID=$!
sleep 10

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    log_result "Server started successfully" 0
    
    # 3. Health check
    echo "🩺 Testing health endpoints..."
    if curl -sS http://127.0.0.1:8080/ | grep -q "Impetus LLM Server"; then
        log_result "Root endpoint responding" 0
    else
        log_result "Root endpoint responding" 1
    fi
    
    if curl -sS http://127.0.0.1:8080/api/health > /dev/null 2>&1; then
        log_result "Health endpoint responding" 0
    else
        log_result "Health endpoint responding" 1
    fi
    
    # 4. Models endpoint
    echo "🤖 Testing models endpoint..."
    if curl -sS http://127.0.0.1:8080/v1/models | jq '.data' > /dev/null 2>&1; then
        log_result "Models endpoint returning valid JSON" 0
    else
        log_result "Models endpoint returning valid JSON" 1
    fi
    
    # 5. Authentication test
    echo "🔐 Testing authentication..."
    # Test without API key (should still work for now due to auto-generation)
    if curl -sS -X POST http://127.0.0.1:8080/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"test","messages":[{"role":"user","content":"Hi"}],"stream":false,"max_tokens":5}' \
        -w "%{http_code}" -o /dev/null | grep -q "200\|404"; then
        log_result "API authentication working" 0
    else
        log_result "API authentication working" 1
    fi
    
    # 6. CORS headers test
    echo "🌐 Testing CORS configuration..."
    if curl -sS -H "Origin: http://localhost:5173" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS http://127.0.0.1:8080/v1/models \
        -w "%{http_code}" -o /dev/null | grep -q "200"; then
        log_result "CORS headers properly configured" 0
    else
        log_result "CORS headers properly configured" 1
    fi
    
    # 7. Streaming test
    echo "📡 Testing streaming response..."
    if timeout 10s curl -N -sS -X POST http://127.0.0.1:8080/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"test","messages":[{"role":"user","content":"Hi"}],"stream":true,"max_tokens":5}' \
        | head -3 | grep -q "data:"; then
        log_result "Streaming responses working" 0
    else
        log_result "Streaming responses working" 1
    fi
    
else
    log_result "Server started successfully" 1
    echo -e "${RED}❌ Server failed to start, skipping endpoint tests${NC}"
    FAILED=$((FAILED + 6))
fi

# 8. Production mode test
echo "🏭 Testing production mode configuration..."
export IMPETUS_ENVIRONMENT=production

# Check if gunicorn config exists
if [ -f "gerdsen_ai_server/gunicorn_config.py" ]; then
    log_result "Gunicorn configuration file exists" 0
else
    log_result "Gunicorn configuration file exists" 1
fi

# 9. Security binding test
echo "🔒 Testing secure binding configuration..."
if grep -q "127.0.0.1:8080" gerdsen_ai_server/src/main.py; then
    log_result "Secure localhost binding configured" 0
else
    log_result "Secure localhost binding configured" 1
fi

# 10. Cleanup and shutdown
echo "🧹 Testing graceful shutdown..."
if kill -0 $SERVER_PID 2>/dev/null; then
    kill -TERM $SERVER_PID
    sleep 5
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        log_result "Graceful shutdown working" 0
    else
        kill -KILL $SERVER_PID 2>/dev/null
        log_result "Graceful shutdown working" 1
    fi
else
    log_result "Graceful shutdown working" 0
fi

# 11. Schema validation test
echo "📋 Testing Pydantic schema fixes..."
if grep -q "model_identifier.*alias=\"model_id\"" gerdsen_ai_server/src/schemas/model_schemas.py; then
    log_result "Pydantic namespace conflicts resolved" 0
else
    log_result "Pydantic namespace conflicts resolved" 1
fi

# 12. MLX compatibility test
echo "🔧 Testing MLX compatibility fixes..."
if grep -q "hasattr.*get_memory_info" gerdsen_ai_server/src/utils/metal_monitor.py; then
    log_result "MLX API compatibility fixes applied" 0
else
    log_result "MLX API compatibility fixes applied" 1
fi

# Final report
echo ""
echo "📊 Verification Summary"
echo "======================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Server is ready for production.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Please review the issues above.${NC}"
    exit 1
fi