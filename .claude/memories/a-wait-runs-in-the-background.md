---
name: a-wait-runs-in-the-background
description: A wait for a workflow run or anything else that takes minutes is a background Bash call or a Monitor, never a foreground sleep, gh run watch or polling loop, so the autopilot reminders keep firing
metadata:
  type: feedback
---

# A wait runs in the background

Waiting for a workflow run, a CloudFront invalidation or anything else that
takes minutes is done with `Bash` and `run_in_background: true`, which notifies
once when the condition holds, or with `Monitor`, which reports each event. It
is never a foreground `sleep`, a foreground `gh run watch` or a polling loop in
the session's own shell.

**Why:** the autopilot's reminders are cron jobs, and a cron job fires only
while the session is idle between turns. A foreground wait holds the session
busy for the whole run, so the standing rules stop arriving exactly while the
session waits on CI, and the user cannot type either. The user set the rule in
`api.10ulabs.com`, `10ulabs.com` took it up on 2026-10-06, and it was adopted
here on 2026-10-07 under issue #255. It used to survive here only as the last
bullet of
[an-etl-is-a-program-beside-its-data](an-etl-is-a-program-beside-its-data.md).

**How to apply:** start the wait in the background, end the turn, and act on the
completion notification. Find the run by its full hash, per
[find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md). While a run is in
progress, idle means idle: no diagnosis, edits or commits meanwhile. Any other
command that can run past a minute follows
[long-running-commands-in-the-background](long-running-commands-in-the-background.md).
