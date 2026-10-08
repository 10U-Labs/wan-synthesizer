---
name: no-ci-skip-in-commit-messages
description: Never suppress a CI run from a commit message; the workflows' paths filters decide what runs, and a skipped run reports neither pass nor fail
metadata:
  type: feedback
---

# No CI-skip directives in commit messages

Never suppress a CI run from a commit message: no `[skip ci]`, `[ci skip]`, `[no
ci]` or any equivalent.

**Why:** the `paths` filters of the workflows under `.github/workflows/` already
decide which workflows a push needs, and CI is the only review there is, per
[commit-straight-to-main](commit-straight-to-main.md) and
[ci-is-the-source-of-truth](ci-is-the-source-of-truth.md). A skipped run reports
neither pass nor fail, so the change it carries is left unverified. The rule
comes from `deltahdl` and was adopted here on 2026-10-07 under issue #255.

**How to apply:** let the path filters do the selecting. If a workflow runs when
it should not, fix its `paths` rather than the commit message.
