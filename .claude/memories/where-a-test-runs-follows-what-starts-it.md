---
name: where-a-test-runs-follows-what-starts-it
description: A test runs in the workflow the change it guards arrives on, not the one that owns its directory
metadata:
  type: project
---

# A test runs in the workflow the change it guards arrives on

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A test about loaded data runs in that data's ETL workflow](#a-test-about-loaded-data-runs-in-that-datas-etl-workflow)
  - [A test about a stack or its deployment runs in that stack's workflow](#a-test-about-a-stack-or-its-deployment-runs-in-that-stacks-workflow)
  - [A test over shared machinery runs where the module is tested](#a-test-over-shared-machinery-runs-where-the-module-is-tested)
  - [The consequence that is accepted](#the-consequence-that-is-accepted)
  - [A test in two workflows needs no cross-listed paths](#a-test-in-two-workflows-needs-no-cross-listed-paths)
  - [The directory and the workflow are separate questions](#the-directory-and-the-workflow-are-separate-questions)

## Overview

A test is worth nothing in a workflow the change it guards does not trigger. So the question "which workflow runs this test" is answered by asking what kind of push would break it, and putting the test where that push goes — not by which subsystem the test file happens to sit under. Which directory it sits under is [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md).

## Conventions

### A test about loaded data runs in that data's ETL workflow

`test/etl/carriers/post_deployment/e2e/test_loaded_carriers.py` reads every carrier back from `api.10ulabs.com` and holds its PoPs and fiber segments to `data/pops` and `data/fiber_segments`. What breaks it is an edit to those CSVs, and a push touching them starts `etl_carriers.yml` and nothing else. That workflow is also what delivers the edit: its `load` job runs the carriers ETL. Deliver and measure are two steps of one thing, and they run in one workflow in that order; the regions and the syntheses are the same shape in `etl_regions.yml` and `etl_syntheses.yml`, and `test/etl/syntheses/pre_deployment/unit/test_configurations.py` holds `etc/` to `data/tenants` in the workflow a push to either starts.

### A test about a stack or its deployment runs in that stack's workflow

`test/www/identity/pre_deployment/unit/` holds the identity stack's declaration to the grants the workflows need, and `test/www/identity/post_deployment/integration/` reads the API key under the reconciled role. Each breaks when `src/www/identity/**` changes, which is what `www_identity.yml` triggers on, and the second runs there after `reconciliation` applies the stack. `test/www/spa/` and `www_spa.yml` are the same for the SPA.

### A test over shared machinery runs where the module is tested

`lib/python/loader` is imported by every ETL and by nothing else in particular, so no one ETL workflow is where it is tested: `scripts.yml` runs `test/lib/python/loader/` under its own coverage gate on every push to `lib/python/**` or `test/**`, and each ETL workflow lists `lib/python/**` so the same push also runs the programs' own tiers; see [shared-modules-are-tested-first](shared-modules-are-tested-first.md).

### A test in two workflows needs no cross-listed paths

A test that already runs in every workflow a change can break needs no further `paths` entry anywhere. Listing a directory under a second workflow's `paths` on top of that once made a style change apply an unrelated stack (`f457a791`). List a directory under a workflow's `paths` only when a change there breaks something that workflow alone runs.

### The consequence that is accepted

A change to the API in `10U-Labs/api.10ulabs.com` is not measured against the data here until the next push that touches something an ETL workflow triggers on, or a `workflow_dispatch` of one.

### The directory and the workflow are separate questions

Which directory the file sits in is answered by what the test checks rather than by what runs it, and the two agreeing is the ordinary case. Where they land apart, the workflow must list that file and its whole conftest chain in its `paths`, or a change to the test does not run the test.
