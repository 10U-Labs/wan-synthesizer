---
name: pylint-refactor-messages-are-hard-failures
description: Every pylint run here passes --fail-on=C,R,W, so the default R limits of 5 arguments, 15 locals, 12 branches and 50 statements are hard limits, and with inline suppression banned the way out is to split the function
metadata:
  type: feedback
---

# pylint refactor messages are hard failures

All eleven pylint invocations in `.github/workflows/` pass `--fail-on=C,R,W`, so
pylint's refactor messages fail the job. Its default limits are hard limits
here: 5 arguments (`too-many-arguments`), 5 positional arguments, 15 locals, 12
branches, 6 returns and 50 statements per function, and 7 instance attributes
per class.

**Why:** `assert-no-inline-directives` fails the run on an inline suppression
and `assert-no-linter-config-files` on a config file that would raise a limit,
so neither way round the limit exists. A function that grows past a limit is a
function to split. The rule comes from the `assert-*` repositories and was
adopted here on 2026-10-07 under issue #255.

**How to apply:** when a change adds a parameter, a local or a branch to a
function near a limit, split the function in the same commit rather than waiting
for the red run: hand a mode's work to a helper, or gather related parameters
into a dataclass. See
[every-workflow-runs-the-assert-tools](every-workflow-runs-the-assert-tools.md).
