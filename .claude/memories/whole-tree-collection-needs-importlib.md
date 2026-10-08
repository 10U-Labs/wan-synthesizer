---
name: whole-tree-collection-needs-importlib
description: "Any pytest run that collects test/ whole passes --import-mode=importlib, because test files share basenames and no test directory has an __init__.py"
metadata:
  node_type: memory
  type: project
  originSessionId: 9a6b8e6c-7338-4a52-8f29-dfbab98cdb2d
  modified: 2026-10-08T02:48:06.634Z
---

# Collecting test/ whole needs --import-mode=importlib

Any pytest run that collects `test/` whole passes `--import-mode=importlib`. No
test directory has an `__init__.py`, so under the default import mode two test
files with one basename get one module name, and collection fails with `import
file mismatch`. Here only `conftest.py` repeats today, four times, but a second
`test_loader.py` or `test_configurations.py` in another subsystem would do the
same. Adopted from `10U-Labs/10ulabs.com` under issue #257 and landed under
issue #259.

**Why:** a run over one subsystem never meets a repeated basename, so nothing
shows the failure until a tool reads the whole tree at once, and
`assert-pytest-fixture-is-requested` in `scripts.yml` does exactly that over
`test/ lib/`. A file that fails to import registers none of its fixture
requests, which is the question
[fixture-liveness-is-a-collection-question](fixture-liveness-is-a-collection-question.md)
leaves to that tool.

**How to apply:** every pytest call in the workflows already passes
`--import-mode=importlib`, and a new one copies it, whether it collects one
subsystem or the whole tree. A whole-tree run also needs `PYTHONPATH` to reach
every import, which is `.:lib/python:src:test` in `scripts.yml`.
