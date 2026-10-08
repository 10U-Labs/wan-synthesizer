---
name: lint-jobs-take-whole-roots
description: "Every Python lint job is scoped to whole roots, src/ lib/ for source and test/ lib/ for tests, never to a list of one stack's paths"
metadata:
  node_type: memory
  type: project
  originSessionId: 9a6b8e6c-7338-4a52-8f29-dfbab98cdb2d
  modified: 2026-10-08T02:47:57.226Z
---

# Lint jobs take whole roots, not path lists

Six workflows run Python lint jobs: the three `etl_*.yml`, `scripts.yml`,
`www_identity.yml` and `www_spa.yml`, the last two only the three test jobs.
Every one of them hands its jobs the same whole roots:

| Job | Scope | Import path |
| --- | --- | --- |
| `copy-paste-source` | `src/ lib/` | none |
| `copy-paste-tests` | `test/ lib/` | none |
| `mypy-source` | `src/ lib/` | `MYPYPATH=lib/python:src` |
| `mypy-tests` | `test/ lib/` | `MYPYPATH=lib/python:src` |
| `pylint-source` | `src/ lib/` | `PYTHONPATH=lib/python:src` |
| `pylint-tests` | `test/ lib/` | `PYTHONPATH=.:lib/python:src` |

`lib/` is on both sides. Adopted from `10U-Labs/10ulabs.com` under issue #257
and landed under issue #259.

**Why:** a job handed one stack and `lib/python` can never see two stacks at
once, so the cross-file checks, jscpd at `--threshold 0` and pylint's `R0801`
under `--fail-on=C,R,W`, cannot fire on code copied from one stack into another.
A path list also leaves a new stack unlinted until someone extends it.

**How to apply:** never write a path list into a lint job; a new stack needs no
edit to any of them. Each job installs what its whole root imports, so a new
third-party import anywhere in `src/` or `lib/` is added to every source job's
install, and one in `test/` to every test job's. Both mypy jobs keep
`--explicit-package-bases`, since four `conftest.py` files under `test/` would
otherwise all be the module `conftest`. The `paths` triggers stay per stack, so
a change in one stack can redden another workflow's lint job without starting
it; widening the triggers is a separate decision.
