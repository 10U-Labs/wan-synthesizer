---
name: code-scanning-is-held-on-by-a-test
description: "CodeQL default setup runs the extended suite over the Python and the JavaScript, and test/documentation holds it configured through the API, so switching it off in the repository settings is red on the next push there"
metadata:
  type: project
---

# Code scanning is held on by a test

Since 2026-09-13 (GitHub issue #216, NIST SP 800-171r3 03.11.02) CodeQL
default setup is `configured` for `javascript-typescript` and `python`
with the `extended` query suite, set through
`gh api -X PATCH repos/10U-Labs/wan-synthesizer/code-scanning/default-setup`
and never through a workflow file, so it runs on every push and weekly
on GitHub's own `CodeQL` workflow.
`test/documentation/pre_deployment/integration/test_code_scanning.py`
reads `code-scanning/analyses` on `main` with `gh api` and holds a
CodeQL analysis of each language to the last eight days and the two
newest to zero results, in `documentation.yml`'s `code-scanning` job
with `security-events: read` and `github.token`. The `default-setup`
endpoint the issue named needs the Administration permission, which
`github.token` never carries and no PAT secret here does, so the query
suite is asserted by nobody and read only by hand:
`gh api repos/10U-Labs/wan-synthesizer/code-scanning/default-setup`.

**Why:** a setting in the repository's web UI is the one gate here with
nothing in the tree to drift from, and the check that cannot be turned
off unnoticed is the test; switching scanning off is red there once the
last analysis is a week old.

**How to apply:** an alert CodeQL raises is a problem met, fixed in the
session that sees it, never dismissed; `gh api
repos/10U-Labs/wan-synthesizer/code-scanning/alerts?state=open` lists
them. The first run raised six `py/incomplete-url-substring-sanitization`
on tests that asked whether `"apigateway.amazonaws.com"` was a substring
of a whole policy, answered by parsing the policy and holding the
principal exactly.
