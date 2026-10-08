---
name: code-is-changed-only-in-this-repository
description: A session edits, commits and pushes only in this repository and never reads another repository's runs; an issue can still be filed in another repository or transferred to it
metadata:
  type: feedback
---

# Code is changed only in this repository

A session here edits, commits and pushes only in `wan-synthesizer`. It does not
change another repository's code, read its workflows or runs, or wait on them.
What it can do in another repository is file an issue there
([file-an-issue-where-it-belongs](file-an-issue-where-it-belongs.md)) or
transfer an issue there
([an-issue-follows-its-code-across-repositories](an-issue-follows-its-code-across-repositories.md)),
since neither changes code.

**Why:** the user decided on 2026-10-07, under issue #256, that a session may
open issues in other repositories but may only write code in this one. Before
that the autopilot followed `blocked_by` links into any repository, worked the
issues it reached there and committed in that repository under this rulebook. It
adapts `api.10ulabs.com`'s reminder that nothing but the repository the session
runs in matters, keeping its rule about other repositories' code and runs while
still letting a session file issues there.

**How to apply:**

- A problem whose code another repository owns, most often `api.10ulabs.com` since the synthesizer moved there, is filed there and goes no further.
- An issue here whose `blocked_by` names an open issue in another repository waits for it. The session reads that issue's state but never works it.
- The autopilot's selection takes only this repository's open issues.
