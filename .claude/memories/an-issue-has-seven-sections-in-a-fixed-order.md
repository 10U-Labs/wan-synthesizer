---
name: an-issue-has-seven-sections-in-a-fixed-order
description: An issue about the program has seven sections in a fixed order, every one of them answered
metadata:
  type: feedback
---

# An issue has seven sections in a fixed order

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [The regression section names the coverage owed](#the-regression-section-names-the-coverage-owed)
  - [Why the closing section is not called Solution](#why-the-closing-section-is-not-called-solution)

## Overview

An issue about the program has seven sections, in this order, and every issue about the program has all seven even when a section is short.

- **Problem** — what is wrong, stated as a fact about the code with the evidence for it.
- **Why Unit Tests Did Not Catch It?** — the specific assertions that passed, and why they could not have failed.
- **Why Integration Tests Did Not Catch It?** — the same, for the tier that checks two units agreeing.
- **Why E2E Tests Did Not Catch It?** — the same, for the tier that makes a caller's journey against the deployed program and judges it on what the caller receives.
- **Why Static Analysis Jobs Did Not Catch It?** — the same, for the half of CI that reads the source without running it: which job saw the file, and why no rule it carries was broken.
- **Which Unit, Integration, or E2E Regression Tests or Static Analysis Jobs Would Prevent This from Happening Again?** — the coverage owed, each test named by the tier it belongs to and the assertion it makes, and each job by the shape it would refuse.
- **Proposed Solution** — the one change to make.

Every heading is in title case. The five that ask something end in a question mark; "Problem" and "Proposed Solution" announce something and do not. Where a tier or a job does not exist for the part of the program in question, saying so is the finding, not a reason to drop the section.

Which issues owe the five in the middle is [[which-issues-owe-the-five-middle-sections]], and why the static analysis one is asked apart from the tiers is [[why-static-analysis-is-asked-separately]]. What the last section may contain is [[an-issue-states-one-solution]].

## Conventions

### The regression section names the coverage owed

Each test entry says which tier the test sits in, what it sets up, and what it asserts, so that the test can be written from the issue without rediscovering the defect. Each job entry says which job gains the rule, what shape it refuses, and whether that job exists yet. The section is separate from the solution because a fix and the coverage that would have caught it are separate pieces of work, and an issue that folds the second into the last paragraph of the first tends to ship without it.

### Why the closing section is not called Solution

Whoever picks the issue up is free to do something else, and "Proposed Solution" says so before they have read a word of it.
