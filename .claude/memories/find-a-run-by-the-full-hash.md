# Find a run by the full commit hash, never the short one

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [An empty list is indistinguishable from a run that has not started](#an-empty-list-is-indistinguishable-from-a-run-that-has-not-started)
  - [Reading a run takes the run id, not a hash](#reading-a-run-takes-the-run-id-not-a-hash)
  - [Two ways to avoid it](#two-ways-to-avoid-it)

## Overview

`gh run list --commit <sha>` matches only the full forty-character hash. Given the abbreviated seven-character form that `git log --oneline` prints and that everybody copies around, it returns an empty list. It does not warn, it does not error, and it does not say that nothing matched.

## Conventions

### An empty list is indistinguishable from a run that has not started

An empty list is exactly what the command returns when a commit genuinely has no runs yet, so the two cannot be told apart from the output alone. A watcher polling until the command reports something waits forever on a short hash, and the waiting looks identical to a run that has not started.

### Reading a run takes the run id, not a hash

`gh run view <run-id>` takes the numeric run id from the listing, not a commit hash of any length, so take the id from the listing rather than constructing a query from the commit.

### Two ways to avoid it

```sh
gh run list --commit "$(git rev-parse HEAD)"
gh run list --limit 10 --json workflowName,status,conclusion,headSha
```

The first passes the full hash, which `git rev-parse` gives and `git log --oneline` does not. The second does not use the filter at all: list the recent runs and match the head SHA by prefix locally. That works with either form of the hash and cannot silently match nothing, which is why it is the right shape for any loop that waits for a conclusion.
