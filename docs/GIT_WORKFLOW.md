# Git Workflow for LipService

**Standard git practices for each sprint and feature**

---

## 🌿 Branch Strategy

### Main Branches
- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features (optional, can skip for small team)

### Feature Branches
For each sprint or feature:
```bash
# Sprint work
git checkout -b sprint/1-project-setup
git checkout -b sprint/2-pattern-analysis

# Specific features
git checkout -b feat/pattern-analyzer
git checkout -b feat/llm-integration
git checkout -b feat/posthog-client

# Bug fixes
git checkout -b fix/policy-validation
git checkout -b fix/redis-connection

# Documentation
git checkout -b docs/api-reference
```

---

## 📝 Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation only
- **style:** Code style (formatting, etc.)
- **refactor:** Code change that neither fixes a bug nor adds a feature
- **test:** Adding or updating tests
- **chore:** Maintenance tasks (dependencies, config)

### Examples
```bash
git commit -m "feat(engine): add pattern clustering with DBSCAN"
git commit -m "fix(api): handle empty log list in analyzer"
git commit -m "docs: update SPRINT_PLAN with Week 2 progress"
git commit -m "test(pattern): add parameterized tests for signatures"
git commit -m "chore: update dependencies to latest versions"
```

### Multi-line Commits
```bash
git commit -m "feat(engine): implement anomaly detection

- Add statistical anomaly detection with Z-score
- Implement sliding window for rate calculation
- Add tests with 95% coverage
- Update API endpoint to expose anomalies

Closes #12"
```

---

## 🔄 Daily Workflow

### Morning: Start Working
```bash
# Make sure you're on latest
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/your-feature
```

### During the Day: Commit Often
```bash
# After completing a small task (every 30-60 minutes)
git add .
git commit -m "feat: add basic pattern analyzer structure"

# Continue working
# ... code more ...

git add .
git commit -m "feat: implement signature generation"

# Keep committing small, logical changes
```

### End of Day: Push to GitHub
```bash
# Push your feature branch
git push origin feat/your-feature

# Or if working on main (for solo development)
git push origin main
```

---

## 📅 Sprint Workflow

### Start of Sprint
```bash
# Create sprint branch
git checkout -b sprint/2-pattern-analysis

# Work on sprint tasks
# Commit frequently
```

### During Sprint
```bash
# After each task completion
git add .
git commit -m "feat(analyzer): implement log signature generation"
git push origin sprint/2-pattern-analysis

# Continue next task
```

### End of Sprint
```bash
# Merge back to main
git checkout main
git merge sprint/2-pattern-analysis
git push origin main

# Tag the release
git tag -a v0.2.0 -m "Sprint 2 complete: Pattern Analysis"
git push origin v0.2.0

# Update TASKS.md to mark sprint complete
git add TASKS.md
git commit -m "docs: mark Sprint 2 as complete"
git push origin main
```

---

## 🔀 Pull Request Workflow (If collaborating)

### Create PR
```bash
# Push feature branch
git push origin feat/your-feature

# Go to GitHub and create PR
# Title: "feat: Add pattern clustering"
# Description: Explain what changed and why
```

### PR Template
```markdown
## What changed?
- Added pattern clustering with DBSCAN
- Implemented signature generation
- Added 15 tests

## Why?
Part of Sprint 2 - Pattern Analysis

## How to test?
pytest tests/test_pattern_analyzer.py

## Checklist
- [x] Tests passing
- [x] Code formatted (ruff format)
- [x] Documentation updated
- [x] No breaking changes
```

---

## 🏷️ Tagging & Releases

### After Each Sprint (Every 2 Weeks)
```bash
# Tag the sprint completion
git tag -a v0.1.0 -m "Sprint 1: Project Setup Complete"
git tag -a v0.2.0 -m "Sprint 2: Pattern Analysis Complete"
git tag -a v0.3.0 -m "Sprint 3: PostHog Integration Complete"

# Push tags
git push origin --tags
```

### Create GitHub Release
After pushing tag, go to GitHub:
1. Click "Releases"
2. "Create a new release"
3. Select your tag (e.g., v0.2.0)
4. Add release notes (what was completed)
5. Publish

---

## 🚨 Emergency Fixes

### Hotfix on Main
```bash
git checkout main
git pull origin main

# Fix the issue
git add .
git commit -m "fix: critical bug in pattern matching"
git push origin main

# Tag if needed
git tag -a v0.2.1 -m "Hotfix: Pattern matching bug"
git push origin --tags
```

---

## 🔍 Useful Git Commands

### Check Status
```bash
git status                    # What's changed?
git log --oneline -5          # Recent commits
git diff                      # What changed in files?
git diff --staged             # What's staged for commit?
```

### Undo Changes
```bash
git restore <file>            # Undo unstaged changes
git restore --staged <file>   # Unstage file
git reset --soft HEAD~1       # Undo last commit (keep changes)
git reset --hard HEAD~1       # Undo last commit (discard changes)
```

### Branch Management
```bash
git branch                    # List local branches
git branch -a                 # List all branches (including remote)
git branch -d feat/old        # Delete merged branch
git checkout -b feat/new      # Create and switch to new branch
```

---

## 📊 Sprint Git Workflow Template

Copy this for each sprint:

### Sprint Start
```bash
# Update from GitHub
git checkout main
git pull origin main

# Create sprint branch (optional)
git checkout -b sprint/X-description

# OR work directly on main for solo dev
```

### During Sprint (Daily)
```bash
# Morning: Pull latest
git pull origin main

# Work, commit often (every 30-60 min)
git add .
git commit -m "feat: descriptive message"

# End of day: Push
git push origin main  # or your feature branch
```

### Sprint End
```bash
# Merge and tag
git checkout main
git merge sprint/X-description  # if using sprint branches
git tag -a v0.X.0 -m "Sprint X: Description"
git push origin main --tags

# Update documentation
git add TASKS.md SPRINT_PLAN.md
git commit -m "docs: mark Sprint X complete, plan Sprint X+1"
git push origin main
```

---

## 🎯 Integration with Sprint Workflow

### Updated Sprint Checklist

Add to each sprint in TASKS.md:

**Git & GitHub:**
- [ ] Create sprint/feature branch
- [ ] Commit frequently (small, logical commits)
- [ ] Push to GitHub daily
- [ ] Tag sprint completion
- [ ] Create GitHub release with notes
- [ ] Update TASKS.md and commit

---

## 🔐 Authentication

### Using HTTPS (Recommended for Windows)
First push will prompt for credentials:
- **Username:** srex-dev
- **Password:** Use a Personal Access Token (not your password)

**Create Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Select scopes: `repo` (all), `workflow`
4. Copy token and save securely
5. Use as password when pushing

### Or Use GitHub CLI
```bash
# Install GitHub CLI: https://cli.github.com/
gh auth login
git push origin main
```

---

## 📌 Best Practices

### DO:
- ✅ Commit often (every 30-60 minutes of work)
- ✅ Write clear commit messages
- ✅ Push to GitHub at end of day
- ✅ Tag sprint completions
- ✅ Keep commits small and focused
- ✅ Test before committing

### DON'T:
- ❌ Commit broken code to main
- ❌ Push secrets or credentials
- ❌ Make huge commits with many changes
- ❌ Use vague messages like "update" or "fix stuff"
- ❌ Force push to main (only on feature branches if needed)

---

## 🎉 Your First Push

After creating the repo on GitHub, run:

```bash
git push -u origin main
```

You should see:
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
...
To https://github.com/srex-dev/lipservice.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

Then visit: **https://github.com/srex-dev/lipservice** 🎉

---

**Ready when you are! Create the repo and let me know, or just run `git push -u origin main`!**

