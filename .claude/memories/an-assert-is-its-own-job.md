---
name: an-assert-is-its-own-job
description: Each assert-* check runs in a job of its own named after its tool, one job per tool per workflow, and a linter job holds only its lint step
metadata:
  type: feedback
---

# An assert is its own job

Each `assert-*` check in a workflow runs in a job of its own, named after the
tool, such as `assert-no-inline-directives` or `assert-no-linter-config-files`.
A linter job, such as `yamllint`, `lint-yaml` or `markdownlint`, holds only its
lint step, and the assert that guards it names the linter in its `tools` or
`linters` input. A workflow cannot hold two jobs of one name, so when one tool
guards several things in a workflow, they share its job: each `etl_*.yml` and
`www_spa.yml` gives its `assert-no-inline-directives` job its own workflow file
beside its Python, with `yamllint` among the `tools`.

**Why:** a job of its own reports as a check of its own, so a red run names the
broken rule without anyone reading a log, and the assert runs alongside the lint
instead of before it. The rule comes from `api.10ulabs.com`, and was adopted
here on 2026-10-07 under issue #262, when seven assert steps came out of the
`yamllint` and `markdownlint` jobs.

**How to apply:** a new assert, or a new linter an existing assert should guard,
goes in the tool's job, which is created when the workflow has none. A job that
deploys or loads lists the new job in its `needs`. Each workflow's unit tests
hold that no job but one named for an `assert-*` tool runs an `assert-*` action,
except `scripts.yml`, which has no workflow test file. How the assert runs is
[an-action-is-preferred-to-a-package-install](an-action-is-preferred-to-a-package-install.md).
