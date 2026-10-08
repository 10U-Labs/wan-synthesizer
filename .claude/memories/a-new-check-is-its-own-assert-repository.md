---
name: a-new-check-is-its-own-assert-repository
description: A rule nothing mechanical checks yet is answered by a new public assert-* repository cloned from the newest one and run in each workflow through the action it publishes, never by a script in this repository; a person creates the repository
metadata:
  type: feedback
---

# A new check is its own assert repository

Every repository-wide rule this organization enforces mechanically lives in its
own public `assert-*` repository in 10U-Labs, published to PyPI with an action
beside it, and each workflow that runs it uses that action, per
[an-action-is-preferred-to-a-package-install](an-action-is-preferred-to-a-package-install.md).
There are twelve as of 2026-10-07, the newest being
`assert-every-dataclass-field-is-read`. A new check does not belong in a script
in this repository or in a test that greps the tree.

To add one, clone the most recently created `assert-*` repository as the
template (`gh repo list 10U-Labs --json name,createdAt`), rename the package and
the CLI throughout, replace the scanner, the samples and the rule's test
classes, and keep `cli.py` as it stands, since it is identical across the
family. PyPI trusted publishing is configured for the organization, so the first
green run of its `release.yml` publishes the package.

**Why:** several memories here end with a section saying nothing mechanical
checks them, and the answer to that is a check, shaped the way every other check
in the organization is shaped. The family shape gives a check full branch
coverage, `mypy --strict`, `pylint --fail-on=C,R,W` and jscpd at threshold 0 for
free, because the template carries those jobs. In `10ulabs.com` an issue once
proposed a script under `scripts/` for a new check, which was the old
convention. The rule was adopted here on 2026-10-07 under issue #255.

**How to apply:** a session files an issue for the new check and leaves creating
the repository to a person. Once it is published, the check is added to every
workflow that should run it, as
[every-workflow-runs-the-assert-tools](every-workflow-runs-the-assert-tools.md)
describes.
