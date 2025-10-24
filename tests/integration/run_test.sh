#!/bin/bash

echo "🎙️ LipService Integration Test Runner"
echo "======================================"
echo ""

# Check if backend is running
echo "🔍 Checking LipService backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ LipService backend is running"
else
    echo "❌ LipService backend not running"
    echo "   Start with: python src/main.py"
    echo ""
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🧪 Running integration test..."
echo "======================================"
echo ""

# Run the simulated test
python tests/integration/test_posthog_integration.py

echo ""
echo "======================================"
echo "✨ Test complete!"
echo ""
echo "💡 To test with real PostHog logs:"
echo "   python tests/integration/test_with_real_posthog_logs.py"

