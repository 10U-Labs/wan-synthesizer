# A rejected push is fixed forward

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Read the whole failed log before pushing the fix](#read-the-whole-failed-log-before-pushing-the-fix)
  - [The tension with solving an issue in one push](#the-tension-with-solving-an-issue-in-one-push)

## Overview

When a push fails CI, fix it in a follow-up commit. Do not amend and force-push. `main` is the only branch and it is already published by the time the run reports, so rewriting it discards the history of what was actually tried.

## Conventions

### Read the whole failed log before pushing the fix

Read all of it rather than its first error, and sweep the change for other instances of the same shape. A fix that clears every sibling instance turns two cycles into one without running anything locally.

### The tension with solving an issue in one push

A single cycle can still hide the next finding where one check's output depends on fixing another, and the tiers behind `test-repo-libraries` wait on the checks. When the two rules collide, CI-only holds and the extra commits are its cost. Local linting has been proposed and declined: no local runs, of anything, including linters.
