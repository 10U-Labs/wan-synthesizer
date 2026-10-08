---
name: a-fix-touches-only-what-must-be-fixed
description: A commit that fixes a red run changes what is broken and nothing else, and never edits another path only to make a workflow run
metadata:
  type: feedback
---

# A fix touches only what must be fixed

A commit that fixes a red run changes what is broken and nothing else. It does
not reach into another path to set off a workflow the fix itself would not fire.

**Why:** `api.10ulabs.com` once had a fix touch a shared path so that every
workflow the red commit had changed ran again. The user rejected that in
`10ulabs.com` on 2026-10-06, holding that a fix touches what must be fixed and
no more, and the rule was adopted here on 2026-10-07 under issue #255. An edit
made only to fire a workflow is a change nobody asked for, and its runs say
nothing about the fix.

**How to apply:** scope the fix to the failure the log names, per
[fixing-a-red-run](fixing-a-red-run.md). Where a workflow has to run again on a
commit, use `gh run rerun` or `workflow_dispatch` instead of an edit; every
workflow here takes `workflow_dispatch`.
