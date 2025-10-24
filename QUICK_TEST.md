# 🚀 Quick Test with Real PostHog Data

**One script to rule them all!**

---

## ⚡ Super Quick Method (Automated)

### **Option 1: Run the Batch Script (Windows)**

```bash
cd C:\Users\jonat\lipservice\tests\integration
RUN_POSTHOG_TEST.bat
```

**This will:**
1. Start PostHog
2. Wait for services to be ready
3. Check for logs
4. Start LipService
5. Run the test
6. Show results

---

## 🔧 Manual Method (If Script Fails)

### **Step 1: Start PostHog (Terminal 1)**

```bash
cd C:\Users\jonat\posthog\posthog
docker-compose -f docker-compose.dev.yml up -d
```

**Wait 3 minutes**, then open: http://localhost:8000

---

### **Step 2: Generate Logs (Browser - 5 minutes)**

Browse PostHog UI:
- Sign up / Log in
- Create a project
- Click around
- View insights
- Browse dashboards

**This creates logs!**

---

### **Step 3: Check Logs Exist**

```bash
docker exec -it posthog-clickhouse-1 clickhouse-client

# In ClickHouse:
SELECT count(*) FROM logs WHERE team_id = 1;

# Should show > 50 logs
# Type 'exit' to quit
```

---

### **Step 4: Start LipService (Terminal 2)**

```bash
cd C:\Users\jonat\lipservice
docker-compose up -d db redis
python src\main.py
```

**Leave this running**

---

### **Step 5: Run Test (Terminal 3)**

```bash
cd C:\Users\jonat\lipservice
python tests\integration\test_with_real_posthog_logs.py
```

---

## 📊 Expected Output

```
🎙️ LipService + PostHog: Real Log Integration Test
===============================================================================

📥 Fetched XXX logs from PostHog

🎯 Sampling Results:
   - Sampled: XX logs (XX%)
   - Dropped: XX logs (XX%)

💰 Cost Savings:
   - Reduction: XX%
   - Monthly: $XX.XX

✨ TEST COMPLETE!
```

---

## 📸 After Test

1. **Take screenshots** of the output
2. **Fill in** `REAL_POSTHOG_TEST_RESULTS.md`
3. **Update** your PostHog GitHub issue
4. **Commit** the results

---

## 🐛 Troubleshooting

### PostHog won't start
```bash
docker ps  # Check what's running
docker-compose logs  # Check errors
```

### No logs in ClickHouse
Browse PostHog more! Every click creates logs.

### Connection refused
Check ClickHouse is running:
```bash
docker ps | grep clickhouse
```

---

## 🎯 Success = Real Numbers!

You'll know it worked when you see:
- ✅ Real log count (not 263)
- ✅ Actual PostHog patterns
- ✅ 70-80% reduction
- ✅ 100% error retention

---

**Ready? Run the script or follow manual steps!** 🚀

