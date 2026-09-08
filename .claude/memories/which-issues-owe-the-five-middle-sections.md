---
name: which-issues-owe-the-five-middle-sections
description: The five middle sections belong to the program; an issue about configs, maps, workflow files or docs has two sections and owes no tests
metadata:
  type: feedback
---

# Which issues owe the five middle sections

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Static analysis reaches both sides and stays with the program](#static-analysis-reaches-both-sides-and-stays-with-the-program)
  - [The test directory falls on both sides](#the-test-directory-falls-on-both-sides)

## Overview

The five sections between the first and the last belong to the program and to nothing else. The program is the code a test tier can run: `src/`, `lib/python/`, `scripts/`, and the OpenTofu under `lib/`. A defect there got past tiers that could have failed, and naming which assertion let it through turns one bug report into a gap in the suite that can be closed.

An issue about the tenant configs in `etc/`, the PoPs and fiber segments in `data/`, the workflow files in `.github/workflows/` or the documentation has two sections, **Problem** and **Proposed Solution**, and owes no tests: a test written against one of them reads a value back and asserts the value it just read, so it cannot fail for a reason worth knowing and goes red every time somebody adds a tenant.

What the seven are is [[an-issue-has-seven-sections-in-a-fixed-order]].

## Conventions

### Static analysis reaches both sides and stays with the program

The YAML linter reads every workflow file and the markdown linter every document, so the static analysis question does have an answer for a defect in one of them. The section stays with the program anyway. The five travel as a set and are answered against one defect between them, and an issue carrying one of the five carries all five; splitting the set so that a documentation issue takes one section and leaves four would put a third shape of issue in the queue, and the reader would have to work out which of the three is in front of them before knowing what the issue owes.

### The test directory falls on both sides

The split is not the directory. The machinery a tier runs on is program code and gets seven sections, conftest fixtures included, because it can make a whole layer report the wrong answer and a unit tier can usually reach it. The assertions themselves get two: asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.
