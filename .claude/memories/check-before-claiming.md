---
name: check-before-claiming
description: Ask gh api before telling the user GitHub cannot do something, and run a tool and read its output before writing what it does into an issue
metadata:
  type: feedback
---

# Check before claiming

Before telling the user that GitHub cannot do something, ask `gh api`. Before
writing into an issue or a memory what a tool does, such as an `assert-*` check,
a linter's default or a workflow's trigger, run it or read its source and its
output.

**Why:** a claim about a tool written from memory reads exactly like one written
from a run, and the next session builds on it. The comparison behind issue #255
found two such claims in its own draft, about which workflows cancel an
in-progress run and what `.gitignore` covers, once the files were read. The rule
merges two `assert-*` memories, `ask-gh-before-saying-github-cannot` and
`run-the-tool-before-writing-the-claim`, and was adopted here on 2026-10-07
under issue #255.

**How to apply:** read the workflow, the tool's `--help`, its source or an API
response before stating what it does, and cite what was read. Tests and linters
are still not run locally, per
[ci-is-the-source-of-truth](ci-is-the-source-of-truth.md); their behaviour is
read off CI or their source.
