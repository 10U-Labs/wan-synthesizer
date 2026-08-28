# Read the test tenets first

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Cover every tier the change touches](#cover-every-tier-the-change-touches)

## Overview

Before implementing a change, read `docs/tenets/tests/` — `OVERVIEW.md`, `UNIT_TESTS.md`, `PRE_DEPLOYMENT_INTEGRATION_TESTS.md`, `POST_DEPLOYMENT_INTEGRATION_TESTS.md` and `E2E_TESTS.md`. They set the rules each tier is held to; the repository's own tree shows where those tiers live, and the tenets deliberately do not restate it. Reading them is the first step of the work, not a check performed afterwards.

## Conventions

### Cover every tier the change touches

Unit tests alone are not sufficient. Add coverage at every tier the change touches. One assert per pytest — an `assert-one-assert-per-pytest` check enforces it in CI.
