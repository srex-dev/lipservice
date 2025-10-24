@echo off
echo ============================================
echo  LipService Real PostHog Integration Test
echo ============================================
echo.

echo Step 1: Starting PostHog services...
echo ============================================
cd C:\Users\jonat\posthog\posthog
echo Starting docker-compose...
docker-compose -f docker-compose.dev.yml up -d

echo.
echo Waiting for PostHog to start (60 seconds)...
timeout /t 60 /nobreak

echo.
echo Step 2: Checking PostHog status...
echo ============================================
docker ps

echo.
echo Step 3: Verifying ClickHouse has logs...
echo ============================================
echo Checking log count in ClickHouse...
docker exec posthog-clickhouse-1 clickhouse-client -q "SELECT count(*) FROM logs WHERE team_id = 1" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: Could not connect to ClickHouse or no logs found
    echo.
    echo Please:
    echo   1. Open http://localhost:8000 in your browser
    echo   2. Browse PostHog for 5 minutes (create project, click dashboards, etc.)
    echo   3. Then run this script again
    echo.
    pause
    exit /b 1
)

echo.
echo Step 4: Starting LipService backend...
echo ============================================
cd C:\Users\jonat\lipservice
echo Starting LipService database and redis...
docker-compose up -d db redis

echo.
echo Waiting for services to be ready (10 seconds)...
timeout /t 10 /nobreak

echo.
echo Step 5: Running integration test with real PostHog data!
echo ============================================
echo.
python tests\integration\test_with_real_posthog_logs.py --clickhouse-host localhost:9000 --team-id 1 --hours 1

echo.
echo ============================================
echo  Test Complete!
echo ============================================
echo.
echo Results saved to: REAL_POSTHOG_TEST_RESULTS.md
echo.
echo Next steps:
echo   1. Review the output above
echo   2. Take screenshots
echo   3. Fill in REAL_POSTHOG_TEST_RESULTS.md with your numbers
echo   4. Update your PostHog GitHub issue
echo.
pause

