---
name: why-static-analysis-is-asked-separately
description: Static analysis is asked about apart from the tiers because a job refuses a shape everywhere at once where a tier catches one occurrence
metadata:
  type: feedback
---

# Why static analysis is asked separately

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Which checks are the jobs](#which-checks-are-the-jobs)
  - [Answering the section](#answering-the-section)

## Overview

Static analysis is the half of CI that reads the source without running it, and it is asked about separately from the tiers because it catches a different kind of defect. A tier executes the program and judges what comes back, so it can only catch what a caller could observe, and it catches it in the one place the test happens to reach. A job reads the text and refuses a shape, so it catches every occurrence of that shape everywhere in the tree at once, and it goes on refusing it in code nobody has written yet. Where the defect is one a rule could have named — an unused definition, a type the caller cannot pass, a duplicated block, a comment — the job is the right answer and a regression test for the single occurrence is the wrong one.

The section this belongs to is in [[an-issue-has-seven-sections-in-a-fixed-order]], and which issues owe it is [[which-issues-owe-the-five-middle-sections]].

## Conventions

### Which checks are the jobs

The linters and the type checkers over source and over tests, the duplicate detector, the YAML and markdown linters, and the `assert-*` checks that carry the rules written here and that no off-the-shelf analyser has. `deploy`, `reconciliation` and `seeding` are not among them, however early they run: they plan and apply against AWS, which makes them the opposite of static.

### Answering the section

Say which job read the file and why nothing it carries was broken. The honest answer is often that every job read the file and none of them has a rule about this, which is what makes the regression section reach for a new one.
