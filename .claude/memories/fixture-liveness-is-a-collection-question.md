---
name: fixture-liveness-is-a-collection-question
description: Never call a pytest fixture dead from a grep or an ast name match; only a collection knows which definition a request resolves to, and only a parse sees getfixturevalue, which is why assert-pytest-fixture-is-requested exists
metadata:
  type: feedback
---

# Fixture liveness is a collection question, not a name match

Whether a pytest fixture is still asked for takes two different reads, and using only one gives wrong answers in both directions.

- **A collection answers reachability.** Only pytest knows which definition a request resolves to: where two conftests publish one name, every requester may resolve to the nearer one and leave the farther one dead. Only pytest knows that a test inside a factory nothing calls never becomes a test.
- **A parse answers `getfixturevalue`.** A collection cannot see a fixture requested by name at run time.

**Why:** in `10ulabs.com` a name match credited four dead fixtures as live, and `pytest-deadfixtures`, which reads no form of `getfixturevalue`, reported live fixtures as dead; deleting two of them turned two post-deployment suites red. The published tools split along exactly this line, which is why `assert-pytest-fixture-is-requested` was built. The rule was adopted here on 2026-10-07 under issue #255.

**How to apply:** never conclude a fixture is dead from a grep or an `ast` walk, and never delete one on that evidence. The question is answered by the `assert-pytest-fixture-is-requested` job in `scripts.yml`, which collects the whole of `test/` and `lib/` with `--import-mode=importlib`, and like every other check it is read off CI, per [ci-is-the-source-of-truth](ci-is-the-source-of-truth.md). How fixtures are named is [every-workflow-runs-the-assert-tools](every-workflow-runs-the-assert-tools.md).
