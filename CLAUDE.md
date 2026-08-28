# Working in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
    - [Seeding races the routing deploy](#seeding-races-the-routing-deploy)
    - [Seeding tests every push](#seeding-tests-every-push)
    - [Shared modules are tested first](#shared-modules-are-tested-first)
    - [Where a test runs follows what starts it](#where-a-test-runs-follows-what-starts-it)
  - [Comments](#comments)
  - [Commits](#commits)
    - [A rejected push is fixed forward](#a-rejected-push-is-fixed-forward)
    - [Commit straight to main](#commit-straight-to-main)
  - [Issues](#issues)
    - [A finding is filed, not mentioned](#a-finding-is-filed-not-mentioned)
    - [An issue has six sections in a fixed order](#an-issue-has-six-sections-in-a-fixed-order)
    - [An issue states one solution](#an-issue-states-one-solution)
    - [Which issues owe the four test sections](#which-issues-owe-the-four-test-sections)
  - [Tests](#tests)
    - [Read the test tenets first](#read-the-test-tenets-first)
    - [The test tree splits on deployment phase](#the-test-tree-splits-on-deployment-phase)
    - [Write the test first](#write-the-test-first)
  - [Third-party code](#third-party-code)
  - [Verification](#verification)
    - [CI is the source of truth](#ci-is-the-source-of-truth)
    - [Find a run by the full hash](#find-a-run-by-the-full-hash)
- [Notes](#notes)

## Overview

These are the standing conventions for working in this repository. Each section links the longer write-up behind it, one note per topic under `.claude/memories/`; [.claude/memories/README.md](.claude/memories/README.md) indexes them all.

## Conventions

### CI workflows

Longer:
[shared-modules-are-tested-first](.claude/memories/shared-modules-are-tested-first.md),
[where-a-test-runs-follows-what-starts-it](.claude/memories/where-a-test-runs-follows-what-starts-it.md),
[seed-tests-every-push](.claude/memories/seed-tests-every-push.md).

#### Seeding races the routing deploy

Adding a new per-tenant store resource can fail the first `seed` run on the new PUT: `seed`, `api_common_routing` and `api_endpoint_tenants` are independent workflows on the same push, so seeding can beat both the route and the handler that stores it. The code says which is behind — `HTTP 403` is a route API Gateway does not define yet, `HTTP 404` is the old handler not knowing the collection. Wait for both, then `gh run rerun <run-id> --failed`. A later commit that misses `etc/`, `openapi.json` and `seed.py` will not re-trigger `seed` at all.

#### Seeding tests every push

Every push that starts `seed.yml` runs every tier, so no run reports success without testing the code that seeds. `reconciliation` and `seeding` wait on every check in their workflow, because they run `tofu apply` and PUT to live AWS and neither can be taken back, so a new check is wired into their `needs:` and their `if:` when it is added. `unit-tests` and `integration-tests` carry `needs: test-repo-libraries` and no `if` at all, and `seeding` names all fifteen gates in one flat `and` beside `github.ref == 'refs/heads/main'` — every job in the workflow but itself and the `e2e-tests` that follows it. `test_seeding_waits_for_every_check_the_workflow_runs` and `test_seeding_demands_a_success_from_every_check_it_waits_for` in `test/scripts/seed/pre_deployment/integration/test_contracts.py` fail when a job is missing from either place. A skip cascades transitively to every descendant and an ordinary expression `if` does not break it, so a job under one that can skip needs its own status-check function, normally `if: ${{ !cancelled() && needs.<parent>.result == 'success' }}` — which is what `e2e-tests` carries against a `seeding` that skips off `main`.

#### Shared modules are tested first

Shared machinery is tested in every workflow that imports it, and before the tests that stand on it. A module under `lib/python/` has no workflow of its own and no single consumer, so its subtree under `test/lib/python/` runs in each workflow whose own tests import it, transitively. Each workflow that runs Python tests carries a `test-repo-libraries` job for this: it starts when the workflow does, runs all nine modules' tests rather than the subset that workflow imports, and is named in the `needs:` of every job there whose tests import them, written out rather than left to arrive down the chain. It gates each module with a `--cov=lib/python/<module>` of its own, so a module arriving without tests fails rather than being carried by its neighbours' numbers, and each workflow lists `test/lib/python/**` in its `paths`. A workflow of its own for these modules cannot be made to work, because GitHub Actions orders nothing between workflows started by the same push.

#### Where a test runs follows what starts it

A test runs in the workflow the change it guards arrives on. Tests about how an API behaves and how its deployment is shaped belong in that endpoint's own workflow. Whether a WAN was actually rebuilt from a change to `etc/` belongs in `seed.yml`, because a push touching `etc/` alone starts `seed.yml` and nothing else, and its `seeding` job is what delivers the change and POSTs the builds. Which directory a test sits in is the separate question of what it checks, and the two agreeing is the ordinary case; where they do not, the workflow must list the file and its whole conftest chain in its `paths`.

### Comments

Longer:
[the-code-is-the-only-explanation](.claude/memories/the-code-is-the-only-explanation.md).

There are no docstrings and no comments anywhere the people here write: not in `src/`, `lib/python/`, `scripts/` or `test/`, not in the `.tf` files or those under `.github/workflows/`, not in `src/www/spa/app.js`, and the `assert-no-comments` job fails the run when one appears. `src/www/spa/vendor/leaflet.js` keeps its comments, like the pinned wheels that ship as `aws_lambda_layer_version.solver`, because nobody here can answer for somebody else's code. Where two mechanisms answer the same question and only one of them is reachable, the unreachable one is deleted rather than documented.

### Commits

#### A rejected push is fixed forward

A push rejected by CI is answered with a follow-up commit. Do not amend and force-push: `main` is published by the time the run reports, and rewriting it discards what was tried. Where this collides with solving an issue in a single push, verifying only in CI is the rule that holds and the extra commits are its cost — local linting has been proposed and declined. Read the whole failed log rather than its first error, and sweep the change for other instances of the same shape before pushing the fix.

#### Commit straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. There is no pull-request buffer, so CI is the only review there is and the tests land in the same commit as the code they cover.

### Issues

Longer:
[how-issues-are-written](.claude/memories/how-issues-are-written.md),
[a-finding-is-filed-not-mentioned](.claude/memories/a-finding-is-filed-not-mentioned.md),
[an-issue-states-one-solution](.claude/memories/an-issue-states-one-solution.md).

#### A finding is filed, not mentioned

A defect noticed while doing something else is filed, not mentioned. Do not end a reply with "one more thing", "two other things I noticed" or "one thing I did not touch": a finding parked in a reply is lost the moment the session ends, nothing links it to the work, and the user is left holding a decision they have to remember to act on. File it in the six-section or two-section shape and then say in one line which number it is. Three cases are not this: something inside the scope of the task in hand is done rather than filed; a finding that reaches a genuine fork is asked about before filing; and a finding that cannot carry a "Problem" section saying what the defect costs is dropped rather than mentioned.

#### An issue has six sections in a fixed order

An issue about the program has six sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It", "Why Integration Tests Did Not Catch It", "Why E2E Tests Did Not Catch It", "Which Unit, Integration, or E2E regression tests would prevent this from happening again?", "Proposed Solution". Every such issue has all six; where a tier does not exist for the part of the program in question, saying so is the finding, not a reason to drop the section. The regression section names the tests to write, each with its tier and its assertion, and is separate from the solution so that a fix cannot ship with the coverage folded into its last paragraph.

#### An issue states one solution

An issue is definitive. Its `Proposed Solution` names one change — this function, this file, this algorithm — because the issue is the instruction to whoever picks it up and they were not in the conversation that produced it. Never file "either X or Y", a menu with a recommendation, or a question left for the reader. Where a draft reaches a genuine fork, stop and ask which branch and then write down the branch that came back, so the asking happens before the filing rather than inside the body. Naming the rejected alternative and why it lost is still worth writing. For issues already on disk that carry an either, do not pick: ask which one before editing a file, however clearly the text leans toward one of them, and ask before there is a draft, because a draft turns the question into a request to approve what is already done.

#### Which issues owe the four test sections

The four test sections belong to the program and to nothing else. The program is what a test tier can run: `src/`, `lib/python/`, `scripts/`, and the OpenTofu under `lib/`. An issue about the configs in `etc/`, the PoPs and fiber segments in `data/`, the workflow files in `.github/workflows/` or the documentation has two sections, "Problem" and "Proposed Solution", and owes no tests — a test over a file no tier runs only reads a value back and asserts what it just read. `test/` falls on both sides: the machinery a tier runs on is program code and gets six, conftest fixtures included, because it can make a whole layer report the wrong answer and a unit tier can usually reach it; the assertions themselves get two, since asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.

### Tests

#### Read the test tenets first

Read `docs/tenets/tests/` before implementing. Unit tests alone are not sufficient: add coverage at every tier the change touches, one assert per pytest. Those docs are tenets: they name no language, tool or directory, and when a tenet and the repository disagree, the repository is what changes.

#### The test tree splits on deployment phase

Every subsystem under `test/` is laid out as `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}`, and a tier directory appears only when a test exists to put in it. The deployment phase is the top split because neither post-deployment tier can be attempted until there is a deployment to call. A journey against a localhost stub is pre-deployment integration however end-to-end it looks: `test/scripts/seed/pre_deployment/integration/test_cli.py` drives `scripts/seed.py` as a subprocess and touches nothing live, while `test/scripts/seed/post_deployment/e2e/test_delivered_syntheses.py` reads the deployed API.

#### Write the test first

We do TDD: the test is written first, then the code that makes it pass. Test-first means authoring order — the red and green observations belong to CI, since nothing runs locally.

### Third-party code

Longer:
[third-party-code-ships-as-a-layer](.claude/memories/third-party-code-ships-as-a-layer.md).

A package the synthesizer needs while it runs ships to AWS as a Lambda layer and is never unpacked into the code this repository publishes. The checks on a push exist to grade what the people here wrote, and a wheel unpacked under `src/` is graded too: `pylint-source`, `mypy-source` and `copy-paste-source` read the synthesizer's own directory, `data "archive_file" "synthesizer"` in `src/api/endpoints/tenants/wan/post/main.tf` zips the whole of that stack's `lambdas/` directory, and the findings that come back are answerable by nobody. `highspy` 1.15.1 and the `numpy` 2.3.5 it needs are pinned by version and by sha256, fetched and unpacked by the workflow before `tofu apply`, and shipped as `aws_lambda_layer_version.solver`, attached to both Lambdas in that stack. The next runtime dependency goes there the same way.

### Verification

#### CI is the source of truth

CI is the source of truth. Do not run tests, linters or builds locally to verify a change — write the code and the tests, commit, push to `main`, and read the run with `gh run list` / `gh run watch` / `gh run view --log-failed`. Local runs cost tokens; CI is free and checks every gate at once. A push can trigger several path-filtered workflows. The change is done when each workflow that fired is green, not when the first one is.

#### Find a run by the full hash

Find the run by the full forty-character hash, from `git rev-parse HEAD`. `gh run list --commit` silently returns an empty list for the short hash `git log --oneline` prints, which is indistinguishable from a run that has not started, so anything that polls should instead run `gh run list --limit 10 --json workflowName,status,conclusion,headSha` and match `headSha` by prefix locally.

## Notes

A convention learned in a session belongs in this repository: a paragraph in this file and a topic file under `.claude/memories/`, linked from both indexes. The session tool's local memory directory is one machine's unversioned files, and a rule kept in both places drifts with nothing to signal it. Keep there only what is true of that machine alone.
