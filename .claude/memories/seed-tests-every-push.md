# Every push that starts seed tests every tier

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A skip cascades unless a status-check function breaks it](#a-skip-cascades-unless-a-status-check-function-breaks-it)
  - [The gates seeding names](#the-gates-seeding-names)
  - [YAML linting stands between a push and the live API](#yaml-linting-stands-between-a-push-and-the-live-api)
  - [Nothing recomputes a decision from the diff](#nothing-recomputes-a-decision-from-the-diff)

## Overview

`.github/workflows/seed.yml` publishes the git-authored inputs to the live API and rebuilds each tenant's WAN, so whatever runs before its `seeding` job is the whole of what stands between a push and a live deploy. Every push that starts the workflow runs all of it, and there is no push that reaches the API having tested less than another one did. A run that tests less reports success without testing the code that seeds: two config commits that moved the tenant knobs under new root keys, after a separate commit had repointed every read in `scripts/seed.py`, left the suite red for four commits with no run saying so.

## Conventions

### A skip cascades unless a status-check function breaks it

A skip cascades transitively wherever one is possible, and an ordinary expression `if` does not break it. Only a status-check function does — `!cancelled()`, `always()`, `success()`, `failure()` — and each descendant needs its own, because breaking the cascade on the parent does not clear it for the child. `seeding` skips off `main`, and `e2e-tests` reads `if: ${{ !cancelled() && needs.seeding.result == 'success' }}` so a skipped `seeding` skips it rather than running it against whatever was last deployed. Failure must block where a skip must pass, and an upstream failure launders into skips further down, so `!failure()` cannot see it there. A positive `== 'success'` reading is what says a branch tail actually succeeded.

### The gates seeding names

`unit-tests` and `integration-tests` carry `needs: test-repo-libraries` and no `if` at all, so a red `test-repo-libraries` skips them both. `seeding` names all fifteen gates in one flat `and` of `== 'success'` readings, beside `github.ref == 'refs/heads/main'`. `test_seeding_waits_for_every_check_the_workflow_runs` and `test_seeding_demands_a_success_from_every_check_it_waits_for` in `test/scripts/seed/pre_deployment/integration/test_contracts.py` fail when a job that is neither `seeding` nor downstream of it is missing from either place, so the next check added is wired in or the run says so.

### YAML linting stands between a push and the live API

The `yamllint` job is the only one that reads the seven tenant configs in `etc/`, which are the inputs `scripts/seed.py` publishes, so a red one is likely to be about a file `seeding` is about to PUT. It is named in `seeding`'s `needs:` and in its `if`.

### Nothing recomputes a decision from the diff

So `gh run rerun` re-runs everything, and `gh workflow run seed.yml --ref main` is the way to start a run for a tip whose last commit touched nothing in `paths`.
