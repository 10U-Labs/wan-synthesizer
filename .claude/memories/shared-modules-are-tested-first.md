---
name: shared-modules-are-tested-first
description: "Every module under lib/python has a test-lib-<module> job in scripts.yml running its own tests under a 100% coverage gate, and a workflow whose program imports a module lists lib/python/** in its paths so a change to the module runs the program's tests too"
metadata:
  type: project
---

# The shared modules are tested before the tests that stand on them

When a shared module is wrong, the run that fails should name the
module. The modules under `lib/python/` — `repo_utils`, which finds the
repository root, and `loader`, which the ETLs are built on — are each
tested by a `test-lib-<module>` job in `scripts.yml` running
`test/lib/python/<module>/` alone with `--cov=lib/python/<module>` at
`--cov-fail-under=100`, so a module that loses coverage fails by name
rather than being carried by a consumer's numbers. `scripts.yml` fires
on `lib/python/**` and `test/**`, and its `mypy-source`,
`pylint-source` and `copy-paste-source` jobs read `lib/python` alone.

**Why:** run a module's tests only inside the `pytest` command of the
tests that import it and a defect in the module reaches the reader as a
failure in whatever tier consumed it, named for that tier's subject,
with no result anywhere naming the module.

**How to apply:**

- A new module is a directory under `lib/python/`, tests under
  `test/lib/python/<module>/pre_deployment/{unit,integration}/`, and a
  `test-lib-<module>` job copied from `test-lib-loader`.
- Every definition in `lib/python` must be named outside its own tests:
  `assert-python-definition-is-used` and its `-outside-own-tests` twin
  in `scripts.yml` search `lib/python`, `src` and `test`, so a constant
  the module keeps for itself is named by its tests, as `loader`'s
  `API_KEY_VARIABLE` and `RETRIED` are.
- A workflow whose program imports a module lists `lib/python/**` in
  its `paths`, as the three `etl_*.yml` do, so a change to the module
  also runs the program's own tiers; GitHub Actions orders nothing
  between workflows started by one push, so the module's job and the
  consumer's run report side by side and the reader opens the one named
  for the module first.

Which workflow a test runs in otherwise is
[where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md).
