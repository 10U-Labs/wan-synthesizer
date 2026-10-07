---
name: writing-code-in-the-main-session
description: The session that holds the autopilot reminders writes the code itself; a subagent never receives them, so subagents are used only for read-only searches
metadata:
  type: feedback
---

# Writing code in the main session

The session that holds the autopilot reminders writes the code, the tests, the workflows and the memories itself. It does not hand an edit to a subagent.

**Why:** the reminders the autopilot skill schedules fire into the main session only. A subagent never receives them and cannot schedule its own, so it reads the rules once and then works unprompted through the longest stretches of a batch, which are the stretches the reminders exist to keep on course. The rule comes from `deltahdl` and was adopted here on 2026-10-07 under issue #255.

**How to apply:** research, write and commit in one session. A subagent is still fine for a read-only search whose conclusion comes back to the main session, such as sweeping the sibling repositories for a pattern. See [a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md).
