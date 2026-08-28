---
name: autopilot
description: Start or stop the standing reminders that keep an autonomous issue-solving session on the rails. Use when the user says "start autopilot", "go autonomous on the open issues", "stop autopilot", or asks to clear the reminders. Takes "start" or "stop".
---

# Autopilot

Eight recurring reminders, one per standing rule, that fire back into this session while it works through open issues on its own. Each rule gets its own reminder so that no rule can be quietly dropped from a merged block of text, and the fire times are staggered across the ten-minute period so they arrive one at a time rather than as a wall.

The argument is the sub-command: `start` or `stop`.

`CronCreate`, `CronList` and `CronDelete` are deferred tools: the session is told their names but not their schemas, so a call made before the schema is fetched fails with `InputValidationError` and creates nothing. Fetch them first with `ToolSearch`, query `select:CronCreate,CronList,CronDelete`: `start` calls `CronCreate`, `stop` calls `CronList` and `CronDelete`.

## Start

Every open issue in the repository the session is running in is in scope, and `start` takes no argument. An issue reached by following a `blocked_by` edge out of that set is in scope as well, whatever repository it lives in, because the two repositories number their issues independently and neither sequence means anything in the other. The floor this used to take was a number below which open issues were left alone, which an edge says better: an issue nobody should work yet is one that genuinely cannot be finished until another is, written down where every reader can see it rather than held as a number one session was told once.

Create eight jobs with `CronCreate`, exactly as listed below. Use `recurring: true` (the default), and take all eight prompts verbatim. Each `cron` field is a distinct offset within the same ten-minute period, so the eight reminders never land together:

| Offset | Cron | Prompt |
| --- | --- | --- |
| :01 | `1,11,21,31,41,51 * * * *` | `REMINDER: Continue to solve the open issues autonomously, unless you need human feedback about ANYTHING — not just about the next open issue.` |
| :03 | `3,13,23,33,43,53 * * * *` | `REMINDER: Issues must be solved through a single commit & push.` |
| :04 | `4,14,24,34,44,54 * * * *` | `REMINDER: Issues must be solved through a set of indivisible tasks, written down with TaskCreate and kept current with TaskUpdate as each one starts and finishes.` |
| :05 | `5,15,25,35,45,55 * * * *` | `REMINDER: Lead with what the thing is for. Every paragraph — in chat as much as in issues, commits and comments — opens with a plain sentence saying what the thing is and what it does, before any file, function or line is named. Say what a defect costs in ordinary words near the top, not in the seventh paragraph. Then cut the details that change nothing the reader would do.` |
| :06 | `6,16,26,36,46,56 * * * *` | `REMINDER: Ensure the tasks you wrote with TaskCreate are indivisible.` |
| :07 | `7,17,27,37,47,57 * * * *` | `REMINDER: Do not do anything but wait while a workflow is running.` |
| :08 | `8,18,28,38,48,58 * * * *` | `REMINDER: A blocked_by edge says this issue cannot be finished until that one is, and nothing else. Add one only where that is true. Most issues you file are blocked by nothing and get no edge, and the edges are not a running order.` |
| :09 | `9,19,29,39,49,59 * * * *` | `REMINDER: When you come up against a new problem, file a GitHub issue, with the sections the Issues section of CLAUDE.md names — six for a problem in the program, which is src/, lib/python/, scripts/ and the OpenTofu under lib/, and two for a problem in a config, a map, a workflow file or the docs, which owes no tests.` |

Then tell the user that eight reminders are running, and the two limits that come with them: the jobs live in this session only and are gone when it ends, and recurring jobs auto-expire after seven days.

Then start working, in the same turn that created the jobs. Read the open issues with `gh issue list`, then read `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` for each of them; every entry names the repository its blocker lives in. Follow those entries, and the entries of the issues they reach, until nothing new comes back, and add every open issue found this way to the set. Then take the lowest-numbered issue in the set that no open issue blocks, preferring the repository the session is running in when two are equally unblocked, and begin solving it under the standing rules the reminders carry — committing in whichever repository its `Proposed Solution` names, and reading that repository's CI to confirm it. Running this skill is starting the work; the eight jobs only keep it on the rails once it is going.

Most open issues block nothing and are blocked by nothing, so that traversal usually hands back the lowest-numbered open issue in this repository. That is the intended answer and not a sign the edges are missing.

An issue filed during a run gets a `blocked_by` edge only where one is true. What that means and how to add it are in the `Issues` section of `CLAUDE.md`, and none of it is particular to autopilot — it holds whenever anybody here files an issue.

What is particular to autopilot is that the traversal reaches another repository only by following an edge into it, and true edges across a repository boundary are rare. A session started here will normally work this repository's issues alone. An issue in `10U-Labs/10ulabs.com` that nothing here genuinely waits on is not reached, and the person who wants it worked has to say so.

## Stop

Call `CronList`, then call `CronDelete` once per job it returns — all of them, not only the eight this skill created. "Delete all your reminders" means the session ends with an empty schedule. Call `CronList` again afterwards to confirm it is empty, and report how many jobs were deleted.

`CronList` returning nothing is not a failure; say the schedule was already empty and stop.

## Notes

Starting autopilot begins the work in the same turn, changed on 2026-08-18. It used to create the eight jobs and stop, on the reasoning that arming the reminders and doing the work were separate things. What that produced was a session sitting idle after `/autopilot start 6`, which is how the command was written while `start` still took a floor: a cron job fires only when the session is idle and the first one is up to ten minutes out, so the skill looked like it had not worked at all. A start at eight minutes past gets going in a minute and looks fine; a start at ten minutes past sits silent for the whole period, and that is the same skill on the same rules.

The three cron tools are deferred, which is why `Start` and `Stop` both open by fetching their schemas. A deferred tool is listed to the session by name only, so the first `CronCreate` call is rejected as invalid input and no job is created — a failure that reads like the tool is missing rather than like a step was skipped.

Cron jobs fire only while the session is idle, never mid-turn, because a turn cannot be preempted. That limit is the reason this skill does not try to correct drift in the middle of a task: what it can do is restart a loop that has stalled, which is the failure it is there to catch.

The reminder at `:09` names no sub-headers of its own, changed on 2026-08-21. It used to spell all six out, matching `CLAUDE.md` and `.claude/memories/how-issues-are-written.md` word for word, and a third copy of a list is a third thing to keep in step: they disagreed on the closing section until 2026-08-02, when the reminder asked for `Proposed Solution` and the other two said `Solution`, and issues #35 and #37 through #55 were all filed with `## Solution` in the meantime. `Proposed Solution` is the name and the two files were changed to it; the seven issues still open that day were rewritten, and the fourteen closed ones keep `## Solution`, since nobody acts on the heading of a finished issue. What the reminder carries now is the part that is genuinely its own — that the sections are owed at all, and that there are six of them for the program and two for everything else — and it points at `CLAUDE.md`, which is in front of the session anyway, for what they are called.

The reminder at `:05` was added on 2026-08-02 for the same reason the two-section form was added to the one at `:09`. The `:09` reminder asks for structure and nothing else, so an issue written to it comes out correctly structured and ordered for whoever wrote it: issue #47 opens by naming `_settled` and the line it sits on, and reaches the race between `seed` and `api_endpoint_tenants_wan_post` that makes the function matter three paragraphs later. Structure is not the whole of how an issue is written, and a reminder that names only structure is read as though it were. `.claude/memories/lead-with-what-it-is-for.md` is the long form, and it applies to chat replies and commit messages too, which is why the reminder does not say "issue".

The `:09` reminder carries the two-section form as well as the six, because it used to carry only the six and firing them alone every ten minutes was enough to produce the tests they asked for. A defect in a workflow file or a config was arriving beside a standing instruction to name the regression tests that would prevent it, and the instruction won: issue #37 had to argue at length that none were owed, and a contract over the seed workflow's yamllint list reached `test/` before the rule was written down. A reminder that names only one case is read as though the case were the whole rule.

The `:04` and `:06` reminders name `TaskCreate` and `TaskUpdate`, changed on 2026-08-22. They used to ask for "a set of indivisible Claude tasks" and that "Claude tasks are indivisible", which names no tool and so reads as a claim about how small a unit of work ought to be — something a session already believes it is doing, and so a reminder that changes nothing. The session started that day took GitHub issue #120 and spent one long turn on a single one of its four regression tests, writing no task down and reporting nothing until it was asked what was going on; both reminders fired throughout, and so did the harness's own notices that the task tools had not been used. What the reminders ask for now is the session's task list, which the user can see.

The skill body is read when the skill is invoked, so editing this file does not reach a session already running under it. Whoever lands a change here has to `/autopilot stop` and `/autopilot start` again before it takes effect: a session that solved the issue which changed this file and then carried on is still working from the scope it was started with, and it will report that it has run out of issues rather than that it is reading the wrong set of them.

`CLAUDE.md` in this repository is the rulebook wherever the session is working, including in another repository the dependency traversal reaches. Verification in CI only, one issue per commit straight to `main`, and the writing and issue-structure rules all hold there. `10U-Labs/10ulabs.com` states none of its own, and a session working there under no rules at all is the worse outcome.

The `:08` reminder used to ask that every filed issue be placed in a total order of `blocked_by` edges, behind the tail of that order when nothing genuinely blocked it, and it forbade leaving an issue with no edge. That rule was removed on 2026-08-23. Auditing the eighteen edges it had produced found exactly one true blocker, #149 behind #148; six edges pointed at issues already closed, and eleven asserted a dependency that reading both issues did not support — among them the chain #144 to #149, six issues editing four unrelated files. An edge that is not true is worse than no edge, because a reader who believes it waits for work that was never in the way, and the reminder was manufacturing them ten times an hour.

The reminder kept its slot and now guards the opposite failure, because the habit it built is the thing most likely to come back. It is not read at invocation and then held: the `:09` reminder fired every ten minutes through the sessions that filed 10ulabs.com#487, 10ulabs.com#488 and #100 without changing what they did.

A reminder in this file is named by the minute it fires — the `:01` reminder, the `:09` reminder — and never by the line it sits on. The eight minutes are the only numbers here a reader can use, and a second set of numbers beside them collides: line 22 is the `:01` reminder, so "the reminder at `:22`" sends a reader looking for one that fires at minute 22, and there is none. This is the same rule GitHub issue #117 settled for the rest of the repository on 2026-08-22, arrived at from the other direction — prose carries the name and not the line number, because the number moves and the name does not.
