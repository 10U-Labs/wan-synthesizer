# Notes for Claude sessions in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
  - [Comments](#comments)
  - [Commits](#commits)
  - [Issues](#issues)
  - [Measurement](#measurement)
  - [Tests](#tests)
  - [Third-party code](#third-party-code)
  - [Verification](#verification)
  - [Vocabulary](#vocabulary)

## Overview

This directory is the rulebook. One memory holds one rule, so a session can recall the one it needs without reading the rest, and each file carries the reasoning behind its rule rather than only the instruction. This index is read at the start of every session and the memories themselves are recalled by relevance, so each line below says enough to know whether the file behind it is the one to open. A convention learned in a session belongs here, as a new memory and a line in this index.

## Conventions

### CI workflows

- [seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md) — a new per-tenant store resource can fail the first `seed` run on the new PUT, and `HTTP 403` and `HTTP 404` say which deploy is behind; a synthesizer change instead fails nothing and grades WANs the old Lambda built, where `--failed` is the wrong re-run
- [seed-tests-every-push](seed-tests-every-push.md) — every push that starts `seed.yml` runs every tier, and how a new check is wired into `reconciliation` and `seeding`
- [shared-modules-are-tested-first](shared-modules-are-tested-first.md) — `test-repo-libraries` runs every module's tests ahead of every job whose tests import them
- [where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md) — a test runs in the workflow the change it guards arrives on

### Comments

- [the-code-is-the-only-explanation](the-code-is-the-only-explanation.md) — no docstrings and no comments anywhere the people here write; `assert-no-comments` fails the run when one appears

### Commits

- [commit-straight-to-main](commit-straight-to-main.md) — direct commits to `main`, no feature branch and no pull request
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a red run is answered with a follow-up commit, never an amend and force-push
- [an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md) — a `Closes #N` line in the commit that solves it, one line per issue; naming an issue in prose references it without closing it

### Issues

- [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md) — a job refuses a shape everywhere at once where a tier catches one occurrence

### Measurement

- [measure-a-change-over-the-seeded-tenants](measure-a-change-over-the-seeded-tenants.md) — every tenant's miles and floor are reproducible from `data/` and `etc/` with no deploy, which is where a commit message's before/after table comes from

### Tests

- [write-the-test-first](write-the-test-first.md) — the test is authored before the code, and red and green are observed in CI
- [cover-every-tier-the-change-touches](cover-every-tier-the-change-touches.md) — unit tests alone are not sufficient, one assert per pytest
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` under every subsystem

### Third-party code

- [third-party-code-ships-as-a-layer](third-party-code-ships-as-a-layer.md) — a package the synthesizer needs at runtime ships as a Lambda layer, never unpacked under `src/`

### Verification

- [ci-is-the-source-of-truth](ci-is-the-source-of-truth.md) — nothing is verified locally; the change is done when every workflow that fired is green
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, so match `headSha` by prefix locally

### Vocabulary

- [a-way-out-of-a-site-is-a-circuit](a-way-out-of-a-site-is-a-circuit.md) — a way out of a site is a circuit, its route is the carrier PoPs it runs through, `path` survives only for files on disk and two graph walks, and ordering and cost are outside the vocabulary
