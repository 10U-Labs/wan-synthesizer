# Verifying in CI, never locally

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Every gate runs in CI, not only pytest](#every-gate-runs-in-ci-not-only-pytest)
  - [The commands that read a run](#the-commands-that-read-a-run)
  - [What it means for TDD and for a change being done](#what-it-means-for-tdd-and-for-a-change-being-done)

## Overview

Do not run tests, linters or builds locally to verify a change. Write the code and the tests, commit, push to `main`, and read the run.

## Conventions

### Every gate runs in CI, not only pytest

The static-analysis jobs, the unit, integration and e2e tiers, and the seed deploy all run from `.github/workflows/`, so a lint sweep is verified by pushing and reading the failed job's log rather than by running an analyser locally file by file. Local runs cost tokens; CI is free and checks everything at once.

### The commands that read a run

`gh run list`, `gh run watch` and `gh run view --log-failed`.

### What it means for TDD and for a change being done

The red-to-green transition is observed in CI rather than on this machine. A change is not done until the triggered workflows are green: this repository has many path-filtered workflows, so one push can start several, and each one that fired has to be read.
