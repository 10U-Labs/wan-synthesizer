---
name: solving-what-a-session-finds
description: File what the session finds as issues of one indivisible problem each, and solve one now only if the work in hand cannot move forward without it
metadata:
  type: feedback
---

# Solving what a session finds

File what you find as issues, each documenting one indivisible problem. Solve
one now only if the work in hand cannot move forward without it; otherwise move
on.

**Why:** this is the autopilot's `:08` reminder, and the rulebook has to say
what the reminder says or a session runs under two rules. An issue makes a
finding durable, where the task list and the scratchpad are not
([research-lives-in-issues](research-lives-in-issues.md)). Solving every finding
on the spot pulls the session off the work in hand for each one, while a filed
issue is picked up by the loop in its turn. The rule comes from `deltahdl`, and
the user adopted it here on 2026-10-07 under issue #256, reversing 1afa1aa9,
which had every problem solved in the session that met it.

**How to apply:**

- File each finding when it arises, unless the commit in hand fixes it or an open issue already covers it ([what-does-not-get-filed](what-does-not-get-filed.md)).
- Give each issue one indivisible problem ([an-issue-is-split-by-problem-not-by-fix](an-issue-is-split-by-problem-not-by-fix.md)): two defects found together are two issues, even where one fix would reach both.
- File it in the repository that owns the code ([file-an-issue-where-it-belongs](file-an-issue-where-it-belongs.md)). One owned elsewhere is never solved here, blocking or not ([code-is-changed-only-in-this-repository](code-is-changed-only-in-this-repository.md)).
- A finding that blocks the work in hand is solved first. In the batch's stack it joins the batch; outside it, it goes in a push of its own before the batch, per [a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md).
- Otherwise carry on with the work in hand and leave the issue to the loop. Write a `blocked_by` link only where something really waits on it.
