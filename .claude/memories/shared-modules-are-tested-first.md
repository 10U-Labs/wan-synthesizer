# The shared modules are tested before the tests that stand on them

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Every workflow runs every module tests](#every-workflow-runs-every-module-tests)
  - [One step per kind of test that exists](#one-step-per-kind-of-test-that-exists)
  - [The job every workflow carries](#the-job-every-workflow-carries)
  - [Two shapes that look right and cannot work](#two-shapes-that-look-right-and-cannot-work)
  - [Why the edges out of the job were kept](#why-the-edges-out-of-the-job-were-kept)

## Overview

When a shared test helper is wrong, the run that fails should name the helper. The nine modules under `lib/python/` are the fixtures, doubles, loaders and readers most of the suite is written on top of. Run them in the same `pytest` command as the tests that import them and a defect in one reaches the reader as a failure in whatever tier consumed it, named for the subject that tier was testing, with no result anywhere naming the module that was wrong. `docs/tenets/tests/OVERVIEW.md`, under "Nothing Is Trusted Before What It Presumes", settles it: the result presuming least is the one that names the defect.

## Conventions

### Every workflow runs every module tests

Not the subset its own tests import. Scoping the job to the import graph makes its contents something nobody maintains, so a new import silently widens what a workflow should have been checking. The modules are pure Python exercised against literals, so the whole of `test/lib/python/` is cheap to run. Every one of those jobs carries the same nine `--cov=lib/python/<module>` flags at `--cov-fail-under=100`, so a module that loses coverage fails rather than being carried by its neighbours' numbers.

### One step per kind of test that exists

Today a unit step over the `pre_deployment/unit/` directories and an integration step over the `pre_deployment/integration/` ones, unit first because it presumes less. `test_http_doubles` is handed its whole `pre_deployment/` directory, both tiers in one argument: the module publishes a stub API server, the code answering a request only runs when a client sends one, and coverage is counted per `pytest` invocation, so a gate seeing only the unit files would report the server untested as covered. There is no `post_deployment/` directory under `test/lib/`, so there is no step for one, and no placeholder step for a directory that is not there.

### The job every workflow carries

Each workflow that runs Python tests carries a job named `test-repo-libraries`. It starts when the workflow does and is named in the `needs:` of every job there whose tests import the modules, written out rather than left to arrive down the chain: an edge that is only transitive disappears the moment somebody redraws the graph. Each workflow also lists `test/lib/python/**` in its `paths`, since a workflow that runs a test file has to be startable by a change to it. In `seed.yml` everything that tests or seeds is behind the job, so nothing is PUT to the live API behind a broken shared module.

### Two shapes that look right and cannot work

A workflow of its own for these modules would run beside the workflows that consume them: GitHub Actions gives no ordering between workflows triggered by the same push. It would report on the modules at the same time as, or after, the tests that already stood on them, which is how a suite ends up green with a red library on the same push. An expression `if` reading the job's result is not a substitute for the `needs:` edge either, because a job that only reads another job's result can start before that job has finished.

### Why the edges out of the job were kept

The tenet fixes what a result means, not what may be attempted, so it does not supply the reason. Two others do: a run that carries on past a broken module spends a `tofu apply` and a seeding pass on results that will be thrown away, and a reader facing a screenful of red consumer jobs has to be told which one to read, where one red job and the rest skipped has already told them.
