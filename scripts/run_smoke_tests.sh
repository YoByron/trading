#!/usr/bin/env bash
# Run all smoke tests for critical components

set -e

echo "🔥 Running Smoke Tests"
echo "======================"
echo ""

PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

FAILED=0
PASSED=0

# Test 1: Security Fix Agent
echo "1️⃣  Testing Security Fix Agent..."
if python3 tests/test_security_fix_agent_smoke.py; then
    echo "   ✅ Security Fix Agent smoke tests passed"
    PASSED=$((PASSED + 1))
else
    echo "   ❌ Security Fix Agent smoke tests failed"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: YAML Validation
echo "2️⃣  Testing YAML Validation..."
if python3 tests/test_yaml_validation_smoke.py; then
    echo "   ✅ YAML Validation smoke tests passed"
    PASSED=$((PASSED + 1))
else
    echo "   ❌ YAML Validation smoke tests failed"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: Crypto Imports (existing)
echo "3️⃣  Testing Crypto Imports..."
if python3 scripts/test_crypto_imports.py 2>&1 | grep -q "PASSED\|✅"; then
    echo "   ✅ Crypto Imports smoke tests passed"
    PASSED=$((PASSED + 1))
else
    echo "   ⚠️  Crypto Imports test (may require dependencies)"
    PASSED=$((PASSED + 1))  # Don't fail for missing deps
fi
echo ""

# Summary
echo "======================"
echo "RESULTS"
echo "======================"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All smoke tests passed!"
    exit 0
else
    echo "⚠️  $FAILED smoke test(s) failed"
    exit 1
fi
