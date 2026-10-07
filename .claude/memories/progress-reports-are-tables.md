---
name: progress-reports-are-tables
description: Report the progress of a running job as a Markdown table with one value per column and the same columns each time, not as a sentence stringing the numbers together
metadata:
  type: user
---

# Progress reports are tables

When reporting the progress of a running job, such as an ETL load, a sweep over issues or a poll, give it as a Markdown table with one value per column (time, done, left, time to go, errors), not as a sentence stringing the numbers together. Leave out a total column, since done plus left already gives it.

**Why:** the user found a progress sentence carrying a count, a total, a remainder, a problem count and a time left hard to read, and asked for a table, in `10ulabs.com` on 2026-10-07. Adopted here on 2026-10-07 under issue #255.

**How to apply:** keep the columns the same from one report to the next so they can be compared, use thousands separators, and give times in local time, per [report-times-in-local-time](report-times-in-local-time.md).
