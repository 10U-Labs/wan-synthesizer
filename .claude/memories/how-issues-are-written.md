# How issues are written

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [The static analysis section](#the-static-analysis-section)
  - [The regression section names the coverage owed](#the-regression-section-names-the-coverage-owed)
  - [Which issues owe the five middle sections](#which-issues-owe-the-five-middle-sections)

## Overview

An issue about the program has seven sections, in this order, and every issue about the program has all seven even when a section is short.

- **Problem** — what is wrong, stated as a fact about the code with the evidence for it.
- **Why Unit Tests Did Not Catch It?** — the specific assertions that passed, and why they could not have failed.
- **Why Integration Tests Did Not Catch It?** — the same, for the tier that checks two units agreeing.
- **Why E2E Tests Did Not Catch It?** — the same, for the tier that makes a caller's journey against the deployed program and judges it on what the caller receives.
- **Why Static Analysis Jobs Did Not Catch It?** — the same, for the half of CI that reads the source without running it: which job saw the file, and why no rule it carries was broken.
- **Which Unit, Integration, or E2E Regression Tests or Static Analysis Jobs Would Prevent This from Happening Again?** — the coverage owed, each test named by the tier it belongs to and the assertion it makes, and each job by the shape it would refuse.
- **Proposed Solution** — the one change to make.

Every heading is in title case. The five that ask something end in a question mark; "Problem" and "Proposed Solution" announce something and do not.

An issue about anything else has two sections, **Problem** and **Proposed Solution**, and owes no tests at all. The closing section is "Proposed Solution" and not "Solution": whoever picks the issue up is free to do something else, and the name says so before they have read a word of it.

## Conventions

### The static analysis section

Static analysis is the half of CI that reads the source without running it, and it is asked about separately from the tiers because it catches a different kind of defect. A tier executes the program and judges what comes back, so it can only catch what a caller could observe, and it catches it in the one place the test happens to reach. A job reads the text and refuses a shape, so it catches every occurrence of that shape everywhere in the tree at once, and it goes on refusing it in code nobody has written yet. Where the defect is one a rule could have named — an unused definition, a type the caller cannot pass, a duplicated block, a comment — the job is the right answer and a regression test for the single occurrence is the wrong one.

The jobs are the linter and the type checker over source and over tests, the duplicate detector, the YAML and markdown linters, and the `assert-*` checks that carry the rules written here and that no off-the-shelf analyser has. `deploy`, `reconciliation` and `seeding` are not among them, however early they run: they plan and apply against AWS, which makes them the opposite of static.

Answering this section means saying which job read the file and why nothing it carries was broken. The honest answer is often that every job read the file and none of them has a rule about this, which is what makes the regression section reach for a new one.

### The regression section names the coverage owed

Each test entry says which tier the test sits in, what it sets up, and what it asserts, so that the test can be written from the issue without rediscovering the defect. Each job entry says which job gains the rule, what shape it refuses, and whether that job exists yet. The section is separate from the solution because a fix and the coverage that would have caught it are separate pieces of work, and an issue that folds the second into the last paragraph of the first tends to ship without it. Answer each backward-looking section honestly, including when the honest answer is that the tier does not exist for that part of the program: that answer is the finding, not a reason to leave the section out.

### Which issues owe the five middle sections

The program is the code a test tier can run: `src/`, `lib/python/`, `scripts/`, and the OpenTofu under `lib/`. A defect there got past tiers that could have failed, and naming which assertion let it through turns one bug report into a gap in the suite that can be closed. The tenant configs under `etc/`, the PoPs and fiber segments under `data/`, the workflow files and the documentation are not the program: a test written against one of them reads a value back and asserts the value it just read, so it cannot fail for a reason worth knowing and goes red every time somebody adds a tenant.

Static analysis is the one thing that reaches both sides, since the YAML linter reads every workflow file and the markdown linter every document, so the question does have an answer for a defect in one of them. The section stays with the program anyway. The five middle sections travel as a set and are answered against one defect between them, and an issue carrying one of the five carries all five; splitting the set so that a documentation issue takes one section and leaves four would put a third shape of issue in the queue, and the reader would have to work out which of the three is in front of them before knowing what the issue owes.

`test/` falls on both sides, and the split is not the directory. The machinery a tier runs on is program code and gets seven sections, conftest fixtures included, because it can make a whole layer report the wrong answer and a unit tier can usually reach it. The assertions themselves get two: asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.
