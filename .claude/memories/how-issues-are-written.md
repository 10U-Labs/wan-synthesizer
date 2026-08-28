# How issues are written

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [How the prose is written](#how-the-prose-is-written)
  - [The regression section names the tests to write](#the-regression-section-names-the-tests-to-write)
  - [Which issues owe the four test sections](#which-issues-owe-the-four-test-sections)

## Overview

An issue about the program has six sections, in this order, and every issue about the program has all six even when a section is short.

- **Problem** — what is wrong, stated as a fact about the code with the evidence for it.
- **Why Unit Tests Did Not Catch It** — the specific assertions that passed, and why they could not have failed.
- **Why Integration Tests Did Not Catch It** — the same, for the tier that checks two units agreeing.
- **Why E2E Tests Did Not Catch It** — the same, for the tier that makes a caller's journey against the deployed program and judges it on what the caller receives.
- **Which Unit, Integration, or E2E regression tests would prevent this from happening again?** — the tests to write, each named by the tier it belongs to and the assertion it makes.
- **Proposed Solution** — the one change to make.

An issue about anything else has two sections, **Problem** and **Proposed Solution**, and owes no tests at all. The closing section is "Proposed Solution" and not "Solution": whoever picks the issue up is free to do something else, and the name says so before they have read a word of it.

## Conventions

### How the prose is written

Simple, plain, ordinary English. Short sentences, one fact each, no hedging, and no jargon from computer science where a plain word will do; assume a network engineer is reading, not a graph theorist. Use telecommunications vocabulary for the subject matter, taking the words for the parts of a backbone from [say-peers-and-circuits](say-peers-and-circuits.md) rather than choosing a synonym here. Each section opens with a plain sentence saying what the thing is and what it is for, and the identifiers follow it; Problem says what the code is there to do before it says what is wrong with it, and says what the defect costs within its first few lines. A detail that changes nothing the reader would do is cut. Back a claim with a number computed from the repository's own data and say how it was computed. Tables where a table genuinely reads better, bullets only when enumerating things, never to break up an argument. No analogies.

### The regression section names the tests to write

Each entry says which tier the test sits in, what it sets up, and what it asserts, so that the test can be written from the issue without rediscovering the defect. It is separate from the solution because a fix and the test that would have caught it are separate pieces of work, and an issue that folds the second into the last paragraph of the first tends to ship without it. Answer each backward-looking section honestly, including when the honest answer is that the tier does not exist for that part of the program: that answer is the finding, not a reason to leave the section out.

### Which issues owe the four test sections

The program is the code a test tier can run: `src/`, `lib/python/`, `scripts/`, and the OpenTofu under `lib/`. A defect there got past tiers that could have failed, and naming which assertion let it through turns one bug report into a gap in the suite that can be closed. The tenant configs under `etc/`, the PoPs and fiber segments under `data/`, the workflow files and the documentation are not the program: a test written against one of them reads a value back and asserts the value it just read, so it cannot fail for a reason worth knowing and goes red every time somebody adds a tenant.

`test/` falls on both sides, and the split is not the directory. The machinery a tier runs on is program code and gets six sections, conftest fixtures included, because it can make a whole layer report the wrong answer and a unit tier can usually reach it. The assertions themselves get two: asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.
