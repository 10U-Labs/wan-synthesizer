---
name: an-issue-follows-its-code-across-repositories
description: "An issue about code that moved to api.10ulabs.com is transferred there with `gh issue transfer`, after it is re-read against the code as it now is; one whose premise the move dissolved is closed with the finding instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8d428965-f87d-438d-9aa6-f8891cff4018
  modified: 2026-09-17T12:15:31.036Z
---

# An issue follows its code across repositories

When the thing an issue describes has moved to another repository of the
organization, the issue is transferred there, not closed here and rewritten
there and not left here pointing across. Before the transfer it is read
against the code where it now lives: an issue the move made false is closed
here with the finding, as [[an-issue-whose-premise-is-false-is-closed-with-the-finding]]
says, and one that still holds is transferred and then its paths, counts
and cross-references are corrected in place.

**Why:** the user's answer on 2026-09-17 to whether the synthesizer issues
should move to `api.10ulabs.com`: "Analyze them deeply first. If they are
still relevant then transfer them." A transfer keeps the history and the
comments and leaves a redirect at the old number; GitHub also rewrites
references to the moved issue in the other issues' bodies, so read a body
back before editing a reference in it.

**How to apply:** `gh label create` any label the target lacks first, or the
transfer drops it. `gh issue view --comments` prints nothing in this
environment; read an issue through `gh api repos/{owner}/{repo}/issues/N`
and its `/comments` instead. Related: [[an-issue-is-closed-by-its-commit]].
