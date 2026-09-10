---
name: autopilot
description: Start or stop the standing reminders that keep an autonomous issue-solving session on the rails. Use when the user says "start autopilot", "go autonomous on the open issues", "stop autopilot", or asks to clear the reminders. Takes "start" or "stop".
---

# Autopilot

Six recurring reminders, one per standing rule, that fire back into this session while it works through open issues on its own. Each rule gets its own reminder so that no rule can be quietly dropped from a merged block of text, and the fire times are staggered across the ten-minute period so they arrive one at a time.

The argument is the sub-command: `start` or `stop`.

`CronCreate`, `CronList` and `CronDelete` are deferred tools: a call made before the schema is fetched fails with `InputValidationError` and creates nothing. Fetch them first with `ToolSearch`, query `select:CronCreate,CronList,CronDelete`.

## Start

Create six jobs with `CronCreate`, exactly as listed below. Use `recurring: true` (the default), and take all six prompts verbatim:

| Offset | Cron | Prompt |
| --- | --- | --- |
| :01 | `1,11,21,31,41,51 * * * *` | `REMINDER: Continue to solve the open issues autonomously, unless you need human feedback about ANYTHING — not just about the next open issue.` |
| :03 | `3,13,23,33,43,53 * * * *` | `REMINDER: Issues must be solved through a single commit & push.` |
| :04 | `4,14,24,34,44,54 * * * *` | `REMINDER: Issues must be solved through a set of indivisible tasks, written down with TaskCreate and kept current with TaskUpdate as each one starts and finishes.` |
| :06 | `6,16,26,36,46,56 * * * *` | `REMINDER: Ensure the tasks you wrote with TaskCreate are indivisible.` |
| :07 | `7,17,27,37,47,57 * * * *` | `REMINDER: Do not do anything but wait while a workflow is running.` |
| :09 | `9,19,29,39,49,59 * * * *` | `REMINDER: When you come up against a problem, solve it. Do not file a GitHub issue about it and move on — a problem you met is a problem you fix, in the same session, under the same standing rules as the issue you were working on.` |

Then tell the user that six reminders are running, and the two limits that come with them: the jobs live in this session only and are gone when it ends, and recurring jobs auto-expire after seven days.

Then start working, in the same turn that created the jobs. Every open issue in the repository the session is running in is in scope, and so is any issue reached by following a `blocked_by` edge out of that set, whatever repository it lives in. Read the open issues with `gh issue list`, then read `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` for each of them and for each issue those entries reach, until nothing new comes back. Take the lowest-numbered issue in the set that no open issue blocks, preferring the repository the session is running in when two are equally unblocked, and solve it — committing in whichever repository its `Proposed Solution` names, and reading that repository's CI to confirm it.

`.claude/memories/` in this repository is the rulebook wherever the session is working, including in another repository the traversal reaches.

## Stop

Call `CronList`, then call `CronDelete` once per job it returns — all of them, not only the six this skill created. Call `CronList` again afterwards to confirm it is empty, and report how many jobs were deleted. `CronList` returning nothing is not a failure; say the schedule was already empty and stop.
