---
name: every-workflow-runs-the-assert-tools
description: "Every workflow runs 10U-Labs' assert-* tools over its own tests beside its lints, scripts.yml collects the whole tree for fixture liveness, every stack workflow holds its OpenTofu resources to being reached, and a fixture takes a name= only where its file binds that name"
metadata:
  type: project
---

# Every workflow runs the assert tools

GitHub issue #237 (2026-09-13) asked whether the workflows should run
the `assert-*` tools `10U-Labs/10ulabs.com` runs and this repository
did not; measured over the tree, five of the six found nothing and
`assert-pytest-fixture-name-is-needed` found 73 fixtures in 18
`conftest.py` files filed under a `name=` nothing in their file bound.
All six run now:

- `assert-no-pytest-plugin-declarations`, `assert-pytest-class-holds-state`,
  `assert-pytest-fixture-name-is-needed` and `assert-pytest-test-can-fail`
  are a job each in every workflow, over the same trees as that
  workflow's `assert-one-assert-per-pytest`, and its deploying job
  needs them.
- `assert-opentofu-resource-is-used` is a job in every stack workflow
  over that stack and `lib/opentofu/common`, searching the whole
  repository for a reference.
- `assert-pytest-fixture-is-requested` collects the whole `test/` tree
  at once, since a fixture in `lib/python` is requested by tests in
  many workflows, so it runs in `scripts.yml`, whose `paths` now cover
  `test/**`.

**Why:** a check that runs where the change arrives is the only one
that goes red on it, per
[where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md),
and a tool nobody runs finds nothing.

**How to apply:** a fixture is a function named for itself,
`@pytest.fixture def stub_api()`, unless something in its file binds
that name — a test's parameter, another fixture's parameter — in which
case it is `@pytest.fixture(name="pauses") def pauses_fixture()`,
which is also what keeps pylint's `redefined-outer-name` quiet. A new
workflow copies the five pytest jobs and, for a stack, the OpenTofu
one, and lists them in its deploying job's `needs`.
