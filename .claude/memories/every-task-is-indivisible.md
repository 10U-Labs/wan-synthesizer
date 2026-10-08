---
name: every-task-is-indivisible
description: Every task on Claude Code's task list is indivisible; a subject naming more than one action is split by action before work starts, judged by the words on the list rather than the purpose behind them
metadata:
  type: feedback
---

# Every task is indivisible

Each task created with `TaskCreate` is one action that cannot be meaningfully
broken down further. A subject that joins several actions, such as format,
stage, commit, push, wait and fix, is divisible by construction, however much
those actions add up to one intent.

**Why:** a divisible task hides its own progress. A subject like "Split the
multi-assert tests" reads as one line whether nine files remain or one, so the
list stops showing the state of the work. Judged by intent, any run of steps
passes as one action, so the check is made on the words. An umbrella verb such
as "Solve #N" or "fix X" names one verb but stands for the test, the change, the
commit, the push and the CI read. The rule merges `tasks-must-be-indivisible`
from the `assert-*` repositories with `deltahdl`'s `one-action-per-task`, and
the user adopted it here on 2026-10-07 under issue #256, with the autopilot's
task-list reminders.

**How to apply:**

- When writing a task, or when the autopilot's indivisibility reminder fires, read each subject and count the actions it names.
- More than one action means a split, one task per action, with the steps already done recorded as completed tasks of their own.
- Split a task in flight the moment it turns out to be divisible.
- A step that may or may not be needed, such as fixing a failing job, is added when the run reports it, not folded into the waiting task.
