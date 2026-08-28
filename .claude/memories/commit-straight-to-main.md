# Committing straight to main

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Commits are the unit work is broken into](#commits-are-the-unit-work-is-broken-into)
  - [Why there is no branch and no pull request](#why-there-is-no-branch-and-no-pull-request)

## Overview

Work goes to `main` as direct commits. Do not create a feature branch, do
not open a pull request, and do not structure advice around a review
cycle. This overrides the default habit of branching before pushing to the
default branch.

## Conventions

### Commits are the unit work is broken into

Use commits as the unit when breaking work down, and think in commit
ordering rather than branch-and-merge.

### Why there is no branch and no pull request

It is a single-maintainer repository and the whole history is
direct-to-main, so a side branch only adds a merge step. CI on `main` is
the verification gate — see
[verification-in-ci-only](verification-in-ci-only.md) — and with no
pull-request buffer it is the only review there is, which is why the tests
land in the same commit as the code they cover.
