---
name: an-action-is-preferred-to-a-package-install
description: "A workflow step runs a tool through its published action, as every assert-* tool and yamllint do, and keeps a pip or npm install only where no action takes what the job needs, as for markdownlint-cli, jscpd, mypy, pylint and pytest"
metadata:
  type: feedback
---

# An action is preferred to a package install

A workflow step runs a tool through the action its project publishes, rather
than installing the package with `pip install` or `npm install` and calling it
in a `run:` step. Every `assert-*` tool runs as `10U-Labs/<tool>@latest`, its
arguments given as inputs and its paths relative to the workspace. Every
workflow's YAML lint runs as `ibiqlik/action-yamllint@v3`, its rules inline as
`config_data` with `strict: "true"`.

**Why:** an action says what a step does in one `uses:` line and carries its own
install, so a job does not spend a step installing what it then runs. The rule
comes from `api.10ulabs.com`, and was adopted here on 2026-10-07 under
issue #258.

**How to apply:** a tool keeps its install only where no published action takes
what the job needs:

- `markdownlint-cli`: the job passes `--disable MD013`, which no action input takes, and a config file would trip `assert-no-linter-config-files`.
- `jscpd`: `kucherenko/jscpd`'s action catches the scan's exit code and never fails, so the jobs' `--threshold 0` could not go red.
- `mypy`: `python/mypy`'s action runs in a virtualenv of its own, which never sees the dependencies the job installs.
- `pylint` and `pytest`: neither project publishes an action.

The 10U-Labs actions are composite and install into the runner's Python, so a
dependency a tool imports, such as the `boto3` and `pytest` that
`assert-pytest-fixture-is-requested` collects with, is installed in an earlier
step and an `env:` on the action's step carries a `PYTHONPATH`.
`ibiqlik/action-yamllint` runs the `yamllint` the runner image carries and
installs nothing. Each workflow's unit tests hold that no step installs an
`assert-*` tool or `yamllint` with pip, except `scripts.yml`, which has no
workflow test file.
