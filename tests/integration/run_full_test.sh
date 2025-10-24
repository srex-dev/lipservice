#!/bin/bash

echo "🎙️ LipService Real PostHog Integration Test"
echo "==========================================="
echo ""

# Check if PostHog is running
echo "📋 Checking prerequisites..."
if ! docker ps | grep -q "posthog-clickhouse"; then
    echo "❌ PostHog ClickHouse not running!"
    echo ""
    echo "Start PostHog first:"
    echo "  cd C:/Users/jonat/posthog/posthog"
    echo "  docker-compose -f docker-compose.dev.yml up -d"
    echo ""
    exit 1
fi

echo "✅ PostHog ClickHouse is running"
echo ""

# Check if LipService backend is running
echo "📋 Checking LipService backend..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  LipService backend not running"
    echo ""
    echo "Start backend in another terminal:"
    echo "  cd C:/Users/jonat/lipservice"
    echo "  python src/main.py"
    echo ""
    echo "Continuing test anyway (SDK will use fallback)..."
fi

echo "✅ Prerequisites checked"
echo ""

# Run the test
echo "🧪 Running real PostHog data test..."
echo "==========================================="
echo ""

python tests/integration/test_with_real_posthog_logs.py \
    --clickhouse-host localhost:9000 \
    --team-id 1 \
    --hours 1 \
    2>&1 | tee real_posthog_test_output.txt

echo ""
echo "==========================================="
echo "✅ Test complete!"
echo ""
echo "Results saved to: real_posthog_test_output.txt"
echo ""
echo "Next steps:"
echo "1. Fill in REAL_POSTHOG_TEST_RESULTS.md with your results"
echo "2. Take screenshots of the output"
echo "3. Update your PostHog GitHub issue with results"
echo ""

