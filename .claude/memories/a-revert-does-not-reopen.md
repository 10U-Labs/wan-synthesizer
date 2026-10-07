---
name: a-revert-does-not-reopen
description: GitHub closes an issue when its closing keyword reaches main and nothing reopens it when that commit is reverted, so a revert is followed by reopening the issue by hand
metadata:
  type: feedback
---

# A revert does not reopen what the commit closed

Reopen an issue by hand when a revert takes back the commit that closed it.

**Why:** GitHub closes an issue when the keyword reaches the default branch and has nothing to undo it. `git revert` writes a new commit and the original stays in history, so the issue stays closed and marked completed whatever the revert's message says. The failure is quiet: the tracker shows finished work, the tree holds none of it, and the autopilot's selection of open issues will never offer it again. The rule comes from `deltahdl` and was adopted here on 2026-10-07 under issue #255.

**How to apply:** a revert is two steps. Push the revert (a forward commit, per [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md)), then `gh issue reopen N` with a comment naming the commit that closed it, the commit that took it back, and what the run said. Read the state back with `gh issue view N --json state`.
