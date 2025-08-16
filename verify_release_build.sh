#!/bin/bash
#
# Release Build Verification Script
# Ensures all production configurations are correct before distribution
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Results tracking
PASSED=0
FAILED=0
TOTAL=0

# Helper function for test results
check_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL=$((TOTAL + 1))
    
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✅ $test_name${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ $test_name${NC}"
        if [ -n "$details" ]; then
            echo -e "${RED}   $details${NC}"
        fi
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${BLUE}🔍 Impetus Release Build Verification${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""

# Test 1: Check default host binding in settings
echo -e "${BLUE}📡 Testing Host Binding Configuration...${NC}"
if grep -q 'default="127.0.0.1"' gerdsen_ai_server/src/config/settings.py; then
    check_result "Settings.py uses secure localhost binding" 0
else
    check_result "Settings.py uses secure localhost binding" 1 "Found insecure default host binding"
fi

# Test 2: Check gunicorn config
if grep -q "127.0.0.1" gerdsen_ai_server/gunicorn_config.py; then
    check_result "Gunicorn config uses secure localhost binding" 0
else
    check_result "Gunicorn config uses secure localhost binding" 1 "Gunicorn still using 0.0.0.0"
fi

# Test 3: Check wsgi config
if grep -q "127.0.0.1" gerdsen_ai_server/wsgi.py; then
    check_result "WSGI config uses secure localhost binding" 0
else
    check_result "WSGI config uses secure localhost binding" 1 "WSGI still using 0.0.0.0"
fi

echo ""
echo -e "${BLUE}🧹 Testing File Exclusions...${NC}"

# Test 4: Check DMG builder excludes test files
if grep -q "rm -rf.*tests" create_professional_dmg.sh; then
    check_result "DMG builder excludes test files" 0
else
    check_result "DMG builder excludes test files" 1 "Tests directory may be included"
fi

# Test 5: Check DMG builder cleans artifacts
if grep -q "find.*__pycache__.*rm" create_professional_dmg.sh; then
    check_result "DMG builder cleans Python artifacts" 0
else
    check_result "DMG builder cleans Python artifacts" 1 "__pycache__ directories may be included"
fi

# Test 6: Check for log file cleanup
if grep -q "*.log.*delete" create_professional_dmg.sh; then
    check_result "DMG builder excludes log files" 0
else
    check_result "DMG builder excludes log files" 1 "Log files may be included"
fi

echo ""
echo -e "${BLUE}🔒 Testing Security Configuration...${NC}"

# Test 7: Check production environment setup
if [[ -f "installers/scripts/launcher.sh" ]] && grep -q "IMPETUS_ENVIRONMENT.*production" installers/scripts/launcher.sh; then
    check_result "Launcher sets production environment" 0
else
    check_result "Launcher sets production environment" 1 "Production environment not set"
fi

# Test 8: Check localhost binding in launcher
if grep -q "IMPETUS_HOST.*127.0.0.1" installers/scripts/launcher.sh; then
    check_result "Launcher forces localhost binding" 0
else
    check_result "Launcher forces localhost binding" 1 "Launcher doesn't force secure binding"
fi

# Test 9: Check debug disabled in launcher
if grep -q "IMPETUS_DEBUG.*false" installers/scripts/launcher.sh; then
    check_result "Launcher disables debug mode" 0
else
    check_result "Launcher disables debug mode" 1 "Debug mode not explicitly disabled"
fi

echo ""
echo -e "${BLUE}⚙️  Testing Production Configuration...${NC}"

# Test 10: Check production config exists
if [[ -f "gerdsen_ai_server/src/config/production.py" ]]; then
    check_result "Production configuration file exists" 0
else
    check_result "Production configuration file exists" 1 "Production config missing"
fi

# Test 11: Check production environment function
if grep -q "configure_production_environment" gerdsen_ai_server/src/config/production.py; then
    check_result "Production environment configuration function exists" 0
else
    check_result "Production environment configuration function exists" 1 "Environment config function missing"
fi

# Test 12: Check security validation function
if grep -q "validate_production_security" gerdsen_ai_server/src/config/production.py; then
    check_result "Security validation function exists" 0
else
    check_result "Security validation function exists" 1 "Security validation function missing"
fi

echo ""
echo -e "${BLUE}📦 Testing DMG Creation...${NC}"

# Test 13: Check DMG script exists and is executable
if [[ -f "create_professional_dmg.sh" ]] && [[ -x "create_professional_dmg.sh" ]]; then
    check_result "DMG creation script is executable" 0
else
    check_result "DMG creation script is executable" 1 "DMG script missing or not executable"
fi

# Test 14: Check production environment indicator
if grep -q "production.*\.environment" create_professional_dmg.sh; then
    check_result "DMG includes production environment indicator" 0
else
    check_result "DMG includes production environment indicator" 1 "Production indicator missing"
fi

echo ""
echo -e "${BLUE}🎯 Testing Asset Files...${NC}"

# Test 15: Check app icon exists
if [[ -f "installers/assets/AppIcon.icns" ]]; then
    check_result "App icon file exists" 0
else
    check_result "App icon file exists" 1 "App icon missing"
fi

# Test 16: Check DMG background exists
if [[ -f "installers/assets/dmg-background.png" ]]; then
    check_result "DMG background image exists" 0
else
    check_result "DMG background image exists" 1 "DMG background missing"
fi

# Test 17: Check Info.plist exists
if [[ -f "installers/assets/Info.plist" ]]; then
    check_result "App bundle Info.plist exists" 0
else
    check_result "App bundle Info.plist exists" 1 "Info.plist missing"
fi

echo ""
echo -e "${BLUE}🧪 Advanced Security Tests...${NC}"

# Test 18: Check no wildcard CORS in settings
if grep -q "cors_origins.*\*" gerdsen_ai_server/src/config/settings.py; then
    check_result "CORS configuration excludes wildcards" 1 "Wildcard CORS found"
else
    check_result "CORS configuration excludes wildcards" 0
fi

# Test 19: Check no test imports in production code
if grep -q "import.*test" gerdsen_ai_server/src/main.py; then
    check_result "Main application excludes test imports" 1 "Test imports found"
else
    check_result "Main application excludes test imports" 0
fi

# Test 20: Check production logging configuration
if grep -q "configure_logging" gerdsen_ai_server/src/config/production.py; then
    check_result "Production logging configuration exists" 0
else
    check_result "Production logging configuration exists" 1 "Production logging config missing"
fi

echo ""
echo -e "${BLUE}📊 Verification Results${NC}"
echo -e "${BLUE}======================${NC}"
echo -e "${GREEN}Passed: $PASSED/${TOTAL}${NC}"
echo -e "${RED}Failed: $FAILED/${TOTAL}${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}Release build is properly configured for production.${NC}"
    echo ""
    echo -e "${BLUE}✅ Security: Localhost-only binding enforced${NC}"
    echo -e "${BLUE}✅ Cleanup: Test files and artifacts excluded${NC}"
    echo -e "${BLUE}✅ Config: Production settings applied${NC}"
    echo -e "${BLUE}✅ Assets: All required files present${NC}"
    echo ""
    echo -e "${GREEN}🚀 Ready to build DMG for distribution!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo -e "${RED}$FAILED issues must be resolved before release.${NC}"
    echo ""
    echo -e "${YELLOW}📋 Action Required:${NC}"
    echo -e "${YELLOW}1. Review failed tests above${NC}"
    echo -e "${YELLOW}2. Fix configuration issues${NC}"
    echo -e "${YELLOW}3. Run verification again${NC}"
    exit 1
fi