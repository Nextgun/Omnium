# Repo Branch Cleanup — April 10, 2026 (DONE)

## Action Table

| Branch | Action | Status |
|--------|--------|--------|
| ~~app-extras~~ | Merged to main | DONE |
| ~~expand-gui~~ | Deleted local | DONE |
| ~~create-exe~~ | Deleted local | DONE |
| ~~integrate-gui~~ | Deleted local | DONE |
| ~~finish-backend~~ | Deleted local | DONE |
| ~~api-layer~~ | Deleted | DONE |
| ~~database~~ | Deleted | DONE |
| ~~merge-and-clean-database~~ | Deleted | DONE |
| ~~claude/repo-cleanup-guide-7Szhi~~ | Deleted | DONE |
| ~~23-sonarqube~~ | Deleted | DONE |
| ~~work-in-progress~~ | Deleted | DONE |
| ~~security-search~~ | Deleted | DONE |
| ~~omnium-standalone~~ | Deleted | DONE |
| ~~sdd-reference~~ | Deleted | DONE |
| ~~feature/tab-and-model-system~~ | Deleted | DONE |
| ~~9-implement-rule-based-trading-algorithm-cs-module~~ | Deleted | DONE |
| ~~11-create-interface-for-switching-between-decision-modules~~ | Deleted | DONE |
| ~~14-design-account-interface-for-future-live-trading-integration~~ | Deleted | DONE |
| **origin/testingbranch** | **Leave alone** | Teammate actively working here; merge after they push |
| **origin/13-implement-logging-of-trades-and-portfolio-tracking** | **Delete remote** | Pending — scratch code, superseded by orchestrator + trades table |

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
| app-extras | 6accceb |
| expand-gui | 7b48ed7 |
| create-exe | d86d509 |
| integrate-gui | d759734 |
| finish-backend | f605810 |
| api-layer | acbb0ce |
| database | b9fb42c |
| merge-and-clean-database | 482b1ac |
| omnium-standalone | 7897997 |

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
