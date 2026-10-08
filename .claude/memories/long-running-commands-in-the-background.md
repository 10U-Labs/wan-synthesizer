---
name: long-running-commands-in-the-background
description: Any command that can take more than about a minute runs as a background Bash call with a time limit and its output in a scratchpad file, and is never followed by a foreground wait
metadata:
  type: feedback
---

# Long-running commands run in the background

Run every command that can take more than about a minute as a background Bash
call (`run_in_background: true`), then end the turn and let its completion
notification resume the work. That covers a sweep of `gh` or `aws` calls over
many issues, runs or log groups, and a long `grep` or `find` over a sibling
repository, as well as the CI wait in
[a-wait-runs-in-the-background](a-wait-runs-in-the-background.md). Tests,
linters and `tofu` are not among them, because per
[ci-is-the-source-of-truth](ci-is-the-source-of-truth.md) they are not run
locally at all.

**Why:** a foreground command holds the turn for as long as it runs, so every
autopilot reminder due in that time waits behind it, and the user cannot type. A
background command frees the turn as soon as it starts. The rule comes from
`deltahdl` by way of `api.10ulabs.com`, and was adopted here on 2026-10-07 under
issue #255.

**How to apply:**

- Give a command that might not end a time limit as well. macOS has no `timeout`, so use `perl -e 'alarm 60; exec @ARGV' <command>`.
- Send the output to a file in the scratchpad and read that file once the notification arrives.
- Never follow a background command with a foreground wait: no `sleep`, no `until` loop, and no rereading its output file until it fills. Any of them blocks the session again.
- Other work that does not depend on the result may go on meanwhile, except while a CI run is in progress, when idle means idle. Once only the result is left to wait for, end the turn.
- A turn made of many short foreground calls also holds the reminders back until it ends. Split long work at its natural boundaries, such as after a batch of edits.
