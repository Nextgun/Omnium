# Repo Cleanup Guide

**Generated:** April 2, 2026 | **Demo Deadline:** April 14, 2026 (12 days)

---

## Branch Cleanup

### Safe to Delete (fully merged)

These branches have **all their commits already in the current codebase**. Delete without worry.

| Branch | Reason |
|--------|--------|
| `app-extras` | Fully merged, 0 unique commits |
| `omnium-standalone` | Fully merged, 0 unique commits |
| `11-create-interface-for-switching-between-decision-modules` | Fully merged, 0 unique commits |

### Likely Safe to Delete (superseded/temporary work)

These branches have unique commits, but the work appears trivial, temporary, or already re-implemented.

| Branch | Unique Commits | Why It's Probably Safe |
|--------|---------------|----------------------|
| `work-in-progress` | 1 — "Temporary: Save all current work" | Explicitly marked temporary |
| `23-sonarqube` | 1 — "From Copilot" | Single Copilot-generated commit |
| `security-search` | 1 — "Add files via upload" | Single file upload, likely superseded |
| `testingbranch` | 4 test commits + main history | Throwaway test commits ("First testing trial", "test") |
| `sdd-reference` | Same 10 commits as main | Appears to be a snapshot/fork of main |
| `14-design-account-interface-for-future-live-trading-integration` | 1 — "Email functionality added" | Email service already exists in current branch (`email_service.py`) |

### Review Before Deleting (may contain unmerged teammate work)

> **These branches have work that may not be in the current codebase. Check with your teammates before deleting.**

| Branch | Unique Commits | What's In There |
|--------|---------------|-----------------|
| `13-implement-logging-of-trades-and-portfolio-tracking` | 7 commits | Trade logging script, Portfolio.py updates. **Ask the teammate who worked on this** if the logging/portfolio tracking has been re-implemented or is still needed. |
| `9-implement-rule-based-trading-algorithm-cs-module` | 2 commits | "Initial CS Algorithm for Day Trading" + SonarQube setup file. The CS algorithm exists in current branch (`cs_algorithm.py`), but **confirm it's the same implementation** and not a different approach. |
| `feature/tab-and-model-system` | 1 commit | "UI: Added ticker tabs and improved layout styling." **WPF UI changes** that may not be in the current MainWindow. Worth a quick diff to check. |

### Keep

| Branch | Reason |
|--------|--------|
| `main` | Primary branch — never delete |
| `database` | Shares divergent history with main; keep until main is updated |

---

## What's Still Not Done

### P0 — Critical for Demo

| Task | Status | Notes |
|------|--------|-------|
| Switch to remote MariaDB (bane.tamucc.edu) | **NOT DONE** | Blocking for shared demo. Need credentials from instructor/admin. ~30 min once you have them. |

### P1 — Should Have

| Task | Status | Notes |
|------|--------|-------|
| Multi-user auth (JWT/sessions) | **NOT DONE** | `auth_system.py` stores `current_user` on the class — breaks with concurrent users. Acceptable for localhost demo, but needs fixing for shared server. Assigned to Brady. |

### P2 — Nice to Have

| Task | Status | Notes |
|------|--------|-------|
| Fix SonarQube CI pipeline | **NOT DONE** | PRs fail on SonarQube step. Likely a path config issue in `sonar-project.properties` after the `src/omnium/` restructure. ~30 min fix. |
| Re-enable git hooks or move to GitHub Actions | **NOT DONE** | Hooks disabled due to team friction. Logic preserved in `setup_dev.py`. |

### Codebase TODOs/FIXMEs

| File | Line | Note |
|------|------|------|
| `src/omnium/__main__.py` | — | Entry point is a placeholder |
| `src/omnium/trading/` | — | Paper trading directory exists but is handled by orchestrator; no standalone module yet |

---

## What's Done (for your sanity)

Everything else on the delivery plan is complete:

- Flask REST API with all endpoints
- MariaDB abstraction layer + schema + seed script
- Login/registration with lockout + email verification
- Asset search, CS algorithm, ML algorithm, algorithm switcher
- Orchestrator, backtesting engine, evaluation/comparison
- Full WPF desktop app (login, real-time refresh, portfolio, backtest, evaluation, about panel)
- Build script (`build.bat`) + launcher (`launch_omnium.bat`)
- Dev setup scripts (`setup_dev.py`, `setup_db.py`)
- Integration tests

---

## Quick Delete Commands

Once you've reviewed the branches above, here are the commands:

```bash
# Delete fully merged branches (safe)
git push origin --delete app-extras
git push origin --delete omnium-standalone
git push origin --delete 11-create-interface-for-switching-between-decision-modules

# Delete likely-safe branches (after confirming with team)
git push origin --delete work-in-progress
git push origin --delete 23-sonarqube
git push origin --delete security-search
git push origin --delete testingbranch
git push origin --delete sdd-reference
git push origin --delete 14-design-account-interface-for-future-live-trading-integration

# Delete after reviewing diffs with teammates
git push origin --delete 13-implement-logging-of-trades-and-portfolio-tracking
git push origin --delete 9-implement-rule-based-trading-algorithm-cs-module
git push origin --delete feature/tab-and-model-system
```
