---
name: no-test-writes-data
description: "no test, in this repository or api.10ulabs.com, creates, changes or deletes data on a deployed service; a post-deployment test only reads"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ab0bb0d3-a72b-4914-8e40-b90e499e86c2
  modified: 2026-10-08T01:56:55.680Z
---

# No test writes data

No test writes data. A post-deployment test reads what the deployed API serves
and never creates, changes or deletes a row there, not even one it cleans up in
teardown. A request a test sends only to be refused (a 400, 401, 403 or 404 with
nothing stored) is not a write.

**Why:** the deployed API is shared. This repository's ETL e2e tests hold that
each listing is exactly what the data under `data/` and `etc/` loads, and a row
another repository's test leaves there, even for minutes, turns them red with
nothing wrong. A deletion does not undo every part of a write either: an id the
store reserved is spent for good, and a synthesis still running cannot be
deleted.

**How to apply:** a red e2e run caused by a row this repository never wrote is
not answered by teaching the test to skip foreign rows. The test that wrote the
row is the defect, and since the API's tests live in `api.10ulabs.com`, it is
filed there per
[an-issue-follows-its-code-across-repositories](an-issue-follows-its-code-across-repositories.md)
and [file-an-issue-where-it-belongs](file-an-issue-where-it-belongs.md).
