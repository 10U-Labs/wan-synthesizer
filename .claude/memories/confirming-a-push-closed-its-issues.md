---
name: confirming-a-push-closed-its-issues
description: Once a push's runs are clean, check that every issue its Closes lines name is closed, because GitHub can land a commit without acting on them
metadata:
  type: feedback
---

# Confirming that a push closed its issues

GitHub can land a commit on `main` without acting on its `Closes #N` lines. In `deltahdl`, a commit naming 64 issues in a 103 KB message closed none of them, while one naming 19 in a 27 KB message closed all of its issues. Whether the count or the size was at fault is not known.

**Why:** an issue left open after its fix landed looks unsolved, so the autopilot takes it up again and works on code that already satisfies it. The rule comes from `10ulabs.com` and `deltahdl`, and was adopted here on 2026-10-07 under issue #255.

**How to apply:** once a push's runs are clean, check every issue its message closes with `gh issue view N --json state`. Close any still open with `gh issue close N --reason completed` and a comment naming the commit that solved it. Keep a batch's message to one paragraph per issue ([a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md)). See [an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md).
