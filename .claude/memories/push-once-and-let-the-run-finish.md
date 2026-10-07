---
name: push-once-and-let-the-run-finish
description: Check gh run list --limit 1 before pushing, because four workflows here cancel an in-progress run on the next push and the three ETL workflows queue behind it; a run is read only once it is completed
metadata:
  type: feedback
---

# Push once and let the run finish

Before pushing, check `gh run list --limit 1` and wait for any run still in progress, per [a-wait-runs-in-the-background](a-wait-runs-in-the-background.md). Read a run only once `gh run view <id> --json status` says `completed`.

**Why:** `documentation.yml`, `scripts.yml`, `www_identity.yml` and `www_spa.yml` set `cancel-in-progress: true`, so a second push while one of them runs cancels the first commit's run, and that commit is never verified or, for `www_identity` and `www_spa`, never deployed by its own run. The three ETL workflows set `cancel-in-progress: false` instead and queue, so a second push makes the second commit's load wait behind the first and makes the two loads impossible to tell apart. A run read before it completes is reported clean while jobs are still pending. The rule comes from `deltahdl`'s `reading-a-ci-run` and the section of that name in `assert-no-comments`'s `CLAUDE.md`, and was adopted here on 2026-10-07 under issue #255.

**How to apply:** one push per body of work, per [a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md), then wait. When the run completes, read every job that did not succeed with `gh run view <id> --log-failed`, not only the first, per [fixing-a-red-run](fixing-a-red-run.md).
