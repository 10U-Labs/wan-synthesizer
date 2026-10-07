---
name: a-failure-outside-the-code-is-re-run
description: A job that failed on a transient download or registry error is re-run with gh run rerun --failed on the same commit, never answered with a follow-up commit that would change nothing
metadata:
  type: feedback
---

# A failure outside the code is re-run, not committed over

A job that failed for a reason outside the code, such as a `setup-*` action's download answering 500, an OpenTofu provider registry answering 504, or a `pip install` or `npm install` that could not reach its index, is re-run on the same commit with `gh run rerun <id> --failed`. It is not answered with a follow-up commit.

**Why:** a follow-up commit would change nothing the failure depended on, and it would fire every workflow its paths touch for no reason, which [a-fix-touches-only-what-must-be-fixed](a-fix-touches-only-what-must-be-fixed.md) rules out. A red gate still has to end green, so the run is repeated rather than left. `api.10ulabs.com` learned this on 2026-09-14, when the OpenTofu release download and the provider registry each failed a run on a commit that was otherwise sound. Adopted here on 2026-10-07 under issue #255.

**How to apply:** read the failed log first, per [fixing-a-red-run](fixing-a-red-run.md), and re-run only when it names the network or a registry rather than the code; if it names the code, fix forward. When the same commit ran a workflow twice, group the runs by workflow before reading a failure: a red run whose twin on the same `headSha` is green has nothing left to fix. After the re-run, wait on the same commit again, per [a-wait-runs-in-the-background](a-wait-runs-in-the-background.md).
