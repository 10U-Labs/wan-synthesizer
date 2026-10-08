---
name: fixing-a-red-run
description: The session whose push goes red fixes it, whether the push caused the failure or inherited it, in a push of its own before the next batch
metadata:
  type: feedback
---

# Fixing a red run after a push

When a run that a push starts goes red, the session that pushed fixes it,
whether the push caused the failure or inherited it from an earlier commit. What
sets the rule off is a push's own run going red, not a red run the session
merely comes across.

**Why:** a change is unverified until the jobs that test it have run, and a
conclusion of `failure` reads the same whether the change broke something or
inherited a break. An inherited failure hides the change's own result for as
long as it stands, and the session that pushed is the one whose change is left
unverified. The rule comes from `10ulabs.com` and `deltahdl`, and was adopted
here on 2026-10-07 under issue #255.

**How to apply:** once every run the push started has completed, read each red
one with `gh run view <id> --log-failed`, listing every job that did not succeed
rather than stopping at the first, and tell a break the change caused from one
it inherited. Fix both kinds forward, per
[a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md),
touching only what the log names, per
[a-fix-touches-only-what-must-be-fixed](a-fix-touches-only-what-must-be-fixed.md).
The fix goes in a push of its own, before the next batch
([a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md)):
pushed together, a second red run could not say whether the fix or the batch
broke it. A job that failed outside the code is re-run rather than fixed, per
[a-failure-outside-the-code-is-re-run](a-failure-outside-the-code-is-re-run.md).
