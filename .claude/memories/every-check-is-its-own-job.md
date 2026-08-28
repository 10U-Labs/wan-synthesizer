# Every check is its own job

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Four edges survive in an api workflow](#four-edges-survive-in-an-api-workflow)
  - [seed.yml gates its checks on nothing](#seedyml-gates-its-checks-on-nothing)
  - [Two costs come with this](#two-costs-come-with-this)

## Overview

A push should tell its author everything that is wrong with it, in one run. A job stops at its first failing step, so while the static-analysis checks were steps of a single job, the checks behind a failure never ran and a change carrying three true findings cost four pushes. Each check is a job of its own now, gated on nothing, installing only the tools it runs. They sit in alphabetical order in the file because `yamllint` runs here with `key-ordering: enable`.

## Conventions

### Four edges survive in an api workflow

- `unit-tests` needs `test-repo-libraries`, and `pre-deployment-integration-tests` needs it too, so that a reader facing red consumers is told which shared module broke them.
- `reconciliation` needs every gate in the workflow, because on `main` it runs `tofu apply` against live AWS. A tier's result can be disbelieved after the fact; an apply cannot be taken back.
- `post-deployment-integration-tests` needs `reconciliation`, because it measures what was deployed.

A green `unit-tests` in a run where `pylint-tests` went red is unestablished rather than a pass, and gating `reconciliation` on every check is what makes the workflow say so: such a run deploys nothing, runs no post-deployment tier, and reports failure.

### seed.yml gates its checks on nothing

`test-repo-libraries` is gated on nothing either, and it is first. `seeding` is `seed.yml`'s `reconciliation`, PUTting the git-authored inputs to the live API, so it names fifteen gates in one flat `and` beside `github.ref == 'refs/heads/main'` — every job in the workflow but itself and the `e2e-tests` that follows it. Two tests in `test/scripts/seed/pre_deployment/integration/test_contracts.py` fail when a job is missing from the `needs:` or from the `if`.

### Two costs come with this

Each job pays its own runner start, checkout and install, so billed minutes go up while wall-clock time comes down. And there are eleven job blocks where there were eleven steps, in nine files, so a change to one check is a change in nine places. One workflow had been linting another workflow's file rather than its own, which is the kind of defect that repetition hides.
