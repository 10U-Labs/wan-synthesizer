---
name: share-code-a-change-mirrors
description: When a change brings two bodies of code or two tests to the same text, share them in the same commit before pushing, because the jscpd jobs run at threshold 0
metadata:
  type: feedback
---

# Share code a change mirrors

When a change brings two places in the tree to the same text, such as two ETL
programs, two handlers in the SPA, or two tests that assert the same things,
move the shared body into one place both call, in the same commit, before
pushing.

**Why:** six workflows here run `copy-paste-source` and `copy-paste-tests` jobs,
`jscpd --threshold 0`, so any duplicated block above jscpd's default size fails
the run. Parallel code is where a fix is most often applied twice, and the ETLs
are parallel by design: `src/etl/carriers/`, `src/etl/regions/` and
`src/etl/syntheses/` share `lib/python/loader` for exactly that reason. Once a
fix makes two bodies equal, the job fails, and the push that follows exists only
to undo the copy. The rule comes from `deltahdl` and was adopted here on
2026-10-07 under issue #255.

**How to apply:** before staging, look for the counterpart of each function or
test the change touched, above all the same file in a sibling ETL. If the change
leaves a run of lines equal in both, move it into one function both call; code
two stacks share goes under `lib/python/`, in a push of its own, per
[shared-modules-are-tested-first](shared-modules-are-tested-first.md) and
[a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md).
For tests, share the fixture rather than the assertions.
