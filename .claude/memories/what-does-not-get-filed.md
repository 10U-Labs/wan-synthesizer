---
name: what-does-not-get-filed
description: A defect the commit in hand fixes is stated in its message, and one an open issue already covers is cited there instead of filed again
metadata:
  type: feedback
---

# What does not get filed

Two findings do not become issues.

- A defect the commit in hand fixes. The commit message states it, and an issue would close on the same push.
- A defect an open issue already covers. Cite that issue instead.

**Why:** a second issue over one defect gives one piece of work two entries, and
closing either leaves the other claiming there is something left. The rule comes
from `deltahdl` and was adopted here on 2026-10-07 under issue #255.

**How to apply:** before filing anything, whether a finding of research
([research-lives-in-issues](research-lives-in-issues.md)) or something the user
asked to have tracked, ask whether the change in hand already closes it, and
search the open issues for one that covers it. Everything else a session finds
is filed, per [solving-what-a-session-finds](solving-what-a-session-finds.md). A
finding about code another repository owns is filed there, per
[file-an-issue-where-it-belongs](file-an-issue-where-it-belongs.md).
