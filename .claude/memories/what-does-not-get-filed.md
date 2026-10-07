---
name: what-does-not-get-filed
description: A problem met while working is solved, not filed; a defect the commit in hand fixes is stated in its message, and one an open issue already covers is cited there instead of filed again
metadata:
  type: feedback
---

# What does not get filed

Three findings do not become issues.

- A problem met while working. The autopilot solves it in the session that meets it, in a push of its own if it lies outside the batch's stack ([a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md)).
- A defect the commit in hand fixes. The commit message states it, and an issue would close on the same push.
- A defect an open issue already covers. Cite that issue instead.

**Why:** a second issue over one defect gives one piece of work two entries, and closing either leaves the other claiming there is something left. A problem parked in an issue rather than fixed is the gap CLAUDE.md says to close, not a record of it. The rule comes from `deltahdl` and was adopted here on 2026-10-07 under issue #255.

**How to apply:** before filing anything, whether a finding of research ([research-lives-in-issues](research-lives-in-issues.md)) or something the user asked to have tracked, ask whether the change in hand already closes it, and search the open issues for one that covers it. A finding about code another repository owns is filed there, per [file-an-issue-where-it-belongs](file-an-issue-where-it-belongs.md).
