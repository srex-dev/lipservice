# ⚡ Daily Development Workflow

**Quick reference for your daily development routine**

---

## ☀️ Morning Routine (5 minutes)

```bash
# 1. Navigate to project
cd C:\Users\jonat\lipservice

# 2. Activate environment
.venv\Scripts\activate

# 3. Pull latest changes
git pull origin main

# 4. Check what's next
cat TASKS.md | Select-String -Pattern "\[ \]" | Select-Object -First 5
```

---

## 💻 Development Loop (Repeat)

### 1. Pick a Task (2 min)
- Open `TASKS.md`
- Choose 1-2 unchecked tasks
- Understand what needs to be done

### 2. Code (30-60 min)
```bash
# Write code for one feature
# Example: Create pattern analyzer class

# Format as you go
ruff format .
```

### 3. Test (5 min)
```bash
# Run tests
pytest

# Check coverage
pytest --cov=src
```

### 4. Commit (2 min)
```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "feat(engine): add pattern signature generation"

# Push to GitHub
git push origin main
```

### 5. Update Progress (1 min)
```bash
# Check off completed task in TASKS.md
# Mark [x] for completed items
```

**Repeat this loop 2-3 times per day!**

---

## 🌙 End of Day Routine (10 minutes)

### 1. Final Commit
```bash
# Make sure everything is committed
git status

# If changes exist
git add .
git commit -m "chore: end of day commit"
git push origin main
```

### 2. Update Documentation
```bash
# Update TASKS.md with progress
git add TASKS.md
git commit -m "docs: update task progress for 2025-01-XX"
git push origin main
```

### 3. Quick Review
- Check GitHub Actions passed
- Review what you completed today
- Plan tomorrow's tasks

---

## 📅 Weekly Routine (Friday, 30 minutes)

### End of Week Review
```bash
# 1. Review completed tasks
cat TASKS.md

# 2. Check GitHub Actions
# Visit: https://github.com/srex-dev/lipservice/actions

# 3. Update sprint documentation
# Edit TASKS.md, mark week complete
```

### If Week 2 Complete → Sprint Complete
```bash
# Tag the sprint
git tag -a v0.1.0 -m "Sprint 1 Complete: Project Setup & Foundation"
git push origin main --tags

# Create GitHub Release
# Go to: https://github.com/srex-dev/lipservice/releases/new
# Select tag: v0.1.0
# Add release notes from TASKS.md
```

---

## 🚨 Common Commands

### Development
```bash
# Start API server
python src\main.py
# Or with auto-reload
uvicorn src.main:app --reload

# Run tests
pytest

# Run specific test
pytest tests/test_api.py::test_health_endpoint_returns_healthy_status

# Format code
ruff format .

# Check linting
ruff check .

# Fix linting issues
ruff check . --fix
```

### Git
```bash
# Check status
git status

# See recent commits
git log --oneline -5

# See what changed
git diff

# Undo unstaged changes
git restore <file>

# Push to GitHub
git push origin main
```

### Docker (Week 2+)
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild
docker-compose build
```

---

## 🎯 Quality Checklist (Before Each Commit)

Quick checklist before committing:

- [ ] Code formatted: `ruff format .`
- [ ] Linting clean: `ruff check .`
- [ ] Tests passing: `pytest`
- [ ] Changes reviewed manually
- [ ] Commit message follows convention
- [ ] Ready to push to GitHub

**Takes 2 minutes, saves hours of debugging!**

---

## 📊 Sprint Progress Tracking

### Check Your Progress
```bash
# See how many tasks left in current sprint
cat TASKS.md | Select-String -Pattern "\[ \]" | Measure-Object

# See how many completed
cat TASKS.md | Select-String -Pattern "\[x\]" | Measure-Object

# See recent commits
git log --oneline -10
```

---

## 🆘 When Things Go Wrong

### Tests Failing
```bash
# Run with verbose output
pytest -v

# Run specific failing test
pytest tests/test_api.py::test_specific_test -v

# Check test coverage
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Linting Errors
```bash
# See all issues
ruff check .

# Auto-fix what's possible
ruff check . --fix

# Format code
ruff format .
```

### Git Issues
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all changes (careful!)
git restore .

# See what branch you're on
git branch

# Switch back to main
git checkout main
```

### GitHub Push Rejected
```bash
# Pull first, then push
git pull origin main
git push origin main

# If conflicts, resolve then:
git add .
git commit -m "merge: resolve conflicts"
git push origin main
```

---

## 🎉 Celebrating Wins

### After Each Task
- ✅ Check off in TASKS.md
- ✅ Commit with good message
- ✅ Take 5-minute break

### After Each Sprint
- ✅ Tag release
- ✅ Create GitHub Release
- ✅ Review what you learned
- ✅ Celebrate progress! 🎊

---

## 🔗 Quick Links

- **GitHub:** https://github.com/srex-dev/lipservice
- **Actions:** https://github.com/srex-dev/lipservice/actions
- **Issues:** https://github.com/srex-dev/lipservice/issues
- **Local API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 💡 Pro Tips

1. **Commit often** - Every 30-60 minutes
2. **Push daily** - Don't lose work
3. **Test first** - Write test, then code
4. **Small changes** - Easier to review and debug
5. **Clear messages** - Future you will thank you
6. **Take breaks** - Step away every hour
7. **Review code** - Before committing

---

**This is your daily rhythm. Stick to it and you'll make steady progress!** 🚀

*Location: C:\Users\jonat\lipservice*  
*Branch: main*  
*Remote: https://github.com/srex-dev/lipservice*

