# Repo Branch Cleanup — April 10, 2026

## Branch Overview

Your main development chain (each branch is an ancestor of the next):

```
api-layer → finish-backend → integrate-gui → create-exe → expand-gui → app-extras (current)
```

`app-extras` is the most advanced branch (51 commits ahead of main, 0 behind expand-gui).
Merging `app-extras` into `main` brings in everything from the entire chain.

---

## Action Table

| Branch | Location | Action | Reason |
|--------|----------|--------|--------|
| **app-extras** | local + remote | **Merge to main** | Latest branch in dev chain; contains all work from api-layer through expand-gui |
| **expand-gui** | local only | **Delete after merge** | Fully contained in app-extras |
| **create-exe** | local only | **Delete after merge** | Fully contained in app-extras |
| **integrate-gui** | local only | **Delete after merge** | Fully contained in app-extras |
| **finish-backend** | local only | **Delete after merge** | Fully contained in app-extras |
| **api-layer** | local + remote | **Delete after merge** | Fully contained in app-extras |
| **database** | local + remote | **Delete now** | Old branch (behind by 9); fully contained in merge-and-clean-database |
| **merge-and-clean-database** | local + remote | **Delete now** | Old branch; fully contained in omnium-standalone |
| **omnium-standalone** | local + remote | **Investigate** | 21 commits ahead of main but on an older parallel chain; may have unique work not in app-extras |
| origin/sdd-reference | remote only | **Delete now** | Points to same commit as origin/main (5b16e90); just a ref copy |
| origin/testingbranch | remote only | **Delete now** | Old testing trial, one commit |
| origin/work-in-progress | remote only | **Investigate** | "Temporary: Save all current work" — check if anything useful is here |
| origin/claude/repo-cleanup-guide-7Szhi | remote only | **Delete now** | Auto-generated cleanup doc; not needed |
| origin/security-search | remote only | **Investigate** | Single upload commit; check if content matters |
| origin/23-sonarqube | remote only | **Delete now** | Copilot-generated SonarQube config; you already have sonar-project.properties |
| origin/feature/tab-and-model-system | remote only | **Investigate** | UI tab/model work; may overlap with or differ from current GUI |
| origin/9-implement-rule-based-trading-algorithm-cs-module | remote only | **Investigate** | CS algorithm work; likely superseded by cs_algorithm.py in app-extras |
| origin/11-create-interface-for-switching-between-decision-modules | remote only | **Investigate** | Switcher/MainWindow refactor; likely superseded by current code |
| origin/13-implement-logging-of-trades-and-portfolio-tracking | remote only | **Investigate** | Logging script; check if this was integrated |
| origin/14-design-account-interface-for-future-live-trading-integration | remote only | **Investigate** | Email functionality; likely superseded by email_service.py |

---

## Commands

### Step 1: Merge app-extras into main

```bash
git switch main
git merge app-extras
git push origin main
```

### Step 2: Delete local branches (safe after merge)

```bash
git branch -d expand-gui
git branch -d create-exe
git branch -d integrate-gui
git branch -d finish-backend
git branch -d api-layer
git branch -d database
git branch -d merge-and-clean-database
```

### Step 3: Delete remote branches (safe to delete now)

```bash
git push origin --delete database
git push origin --delete merge-and-clean-database
git push origin --delete api-layer
git push origin --delete sdd-reference
git push origin --delete testingbranch
git push origin --delete claude/repo-cleanup-guide-7Szhi
git push origin --delete 23-sonarqube
```

### Step 4: Delete remote branches (after merge)

```bash
git push origin --delete app-extras
git push origin --delete expand-gui
```

Note: expand-gui only exists locally, so only delete the remote if it exists.

---

## How to Revert Everything

### Restore a deleted local branch

If you just deleted it and haven't run `git gc`, use reflog:

```bash
git reflog
# Find the commit hash for the branch tip, then:
git switch -c <branch-name> <commit-hash>
```

Known commit hashes for reference:

| Branch | Commit |
|--------|--------|
| expand-gui | 7b48ed7 |
| create-exe | d86d509 |
| integrate-gui | d759734 |
| finish-backend | f605810 |
| api-layer | acbb0ce |
| database | b9fb42c |
| merge-and-clean-database | 482b1ac |

Example:
```bash
git switch -c expand-gui 7b48ed7
```

### Restore a deleted remote branch

Push the branch back using the saved commit hash:

```bash
git push origin <commit-hash>:refs/heads/<branch-name>
```

Example:
```bash
git push origin b9fb42c:refs/heads/database
```

### Undo the merge to main

```bash
git switch main
git log --oneline -5
# Find the commit hash that was the tip of main BEFORE the merge, then:
git reset --hard <pre-merge-commit-hash>
git push origin main --force
```

**Warning:** Force-pushing main rewrites shared history. Only do this if no one else has pulled the merged main.

---

## Branches to Investigate Before Deleting

These branches may have teammate work that wasn't merged into the main dev chain. Before deleting, compare them:

```bash
# See what unique commits a branch has vs app-extras:
git log app-extras..<branch-name> --oneline

# For remote-only branches:
git log app-extras..origin/<branch-name> --oneline
```

Branches to check:
- `omnium-standalone` — older parallel chain, 21 ahead of main
- `origin/work-in-progress` — temporary save
- `origin/security-search` — uploaded files
- `origin/feature/tab-and-model-system` — UI work
- `origin/9-implement-rule-based-trading-algorithm-cs-module` — CS algo
- `origin/11-create-interface-for-switching-between-decision-modules` — switcher refactor
- `origin/13-implement-logging-of-trades-and-portfolio-tracking` — logging
- `origin/14-design-account-interface-for-future-live-trading-integration` — email/account
