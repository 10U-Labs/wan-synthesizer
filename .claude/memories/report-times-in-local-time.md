---
name: report-times-in-local-time
description: Give the user times in the machine's local timezone as date prints it (US Eastern), never in UTC
metadata:
  type: user
---

# Report times in local time

When telling the user a time, such as a progress line, when a run started or when something should finish, give it in the local machine's timezone as `date` prints it (US Eastern, EDT or EST), never in UTC. A status script whose lines the user reads prints `date +'%-I:%M:%S %p %Z'`, not `date -u`.

**Why:** the user asked in `10ulabs.com` on 2026-10-07 for progress in the machine's timezone rather than UTC. GitHub's `createdAt` and every AWS timestamp are UTC, so the conversion is easy to skip. Adopted here on 2026-10-07 under issue #255.

**How to apply:** convert any UTC time from GitHub, AWS or a log before stating it. See [progress-reports-are-tables](progress-reports-are-tables.md).
