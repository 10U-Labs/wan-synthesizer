# Notes for Claude sessions in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
  - [Comments](#comments)
  - [Commits](#commits)
  - [Issues](#issues)
  - [Measurement](#measurement)
  - [Login](#login)
  - [Identity](#identity)
  - [Memories](#memories)
  - [Storage](#storage)
  - [Tests](#tests)
  - [Third-party code](#third-party-code)
  - [Verification](#verification)
  - [Vocabulary](#vocabulary)

## Overview

This directory is the rulebook. One memory holds one rule, so a session can recall the one it needs without reading the rest, and each file carries the reasoning behind its rule rather than only the instruction. This index is read at the start of every session and the memories themselves are recalled by relevance, so each line below says enough to know whether the file behind it is the one to open. A convention learned in a session belongs here, as a new memory and a line in this index.

## Conventions

### CI workflows

- [seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md) — a new per-tenant store resource can fail the first `seed` run on the new PUT, and `HTTP 403` and `HTTP 404` say which deploy is behind; a synthesizer change instead fails nothing and grades WANs the old Lambda built, where `--failed` is the wrong re-run; the prune keeps every key the run wrote, so a rename never races it
- [seeding-waits-for-every-deploy](seeding-waits-for-every-deploy.md) — `seeding` runs after every workflow on the same commit that deploys something it talks to, through a wait job copied from `10ulabs.com`, so a seed never grades WANs the previous Lambda built
- [seed-tests-every-push](seed-tests-every-push.md) — every push that starts `seed.yml` runs every tier, and how a new check is wired into `reconciliation` and `seeding`
- [shared-modules-are-tested-first](shared-modules-are-tested-first.md) — `test-repo-libraries` runs every module's tests ahead of every job whose tests import them
- [where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md) — a test runs in the workflow the change it guards arrives on, and one that already runs in two needs no cross-listed `paths`

### Comments

- [the-code-is-the-only-explanation](the-code-is-the-only-explanation.md) — no docstrings and no comments anywhere the people here write; `assert-no-comments` fails the run when one appears

### Commits

- [commit-straight-to-main](commit-straight-to-main.md) — direct commits to `main`, no feature branch and no pull request
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a red run is answered with a follow-up commit, never an amend and force-push
- [push-over-ssh-not-https](push-over-ssh-not-https.md) — an HTTPS push carrying a workflow file is refused for want of the `workflow` scope, and the fix is the remote URL rather than the token
- [an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md) — a `Closes #N` line in the commit that solves it, one line per issue; naming an issue in prose references it without closing it
- [an-issue-whose-premise-is-false-is-closed-with-the-finding](an-issue-whose-premise-is-false-is-closed-with-the-finding.md) — a defect the code cannot produce is closed by a comment with the argument and the measurement, never by a behaviour-identical refactor whose test cannot go red

### Issues

- [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md) — a job refuses a shape everywhere at once where a tier catches one occurrence
- [the-description-check-reads-only-identifiers](the-description-check-reads-only-identifiers.md) — `assert-description-identifiers-exist` holds a served description that spells a snake_case identifier the tree lost, and a description naming a retired field in prose is held by reading

### Measurement

- [measure-a-change-over-the-seeded-tenants](measure-a-change-over-the-seeded-tenants.md) — every tenant's miles and floor are reproducible from `data/` and `etc/` with no deploy, which is where a commit message's before/after table comes from

### Login

- [the-api-admits-a-google-account-or-the-seed-key](the-api-admits-a-google-account-or-the-seed-key.md) — every operation but a preflight sits behind the routing stack's authorizer, which admits a Google ID token for a `10ulabs.com` account named in `/wan-synthesizer/authorized-accounts` (set through the repository variable `WAN_SYNTHESIZER_AUTHORIZED_ACCOUNTS`) or the API key CI reads from SSM as `WAN_SYNTHESIZER_API_KEY`, which is granted every read and only the writes `seed.py` makes, tabled as `SEED_WRITES`; the SPA and `authorizer.tf` must agree on the OAuth client, every route the map fetches needs an `options` mock, the page opens on the sign-in screen alone, and the name in Google's chooser is the Cloud project's branding

### Identity

- [the-deploy-role-is-narrowed-by-its-own-stack](the-deploy-role-is-narrowed-by-its-own-stack.md) — `TenULabsWanSynthesizerRole` is declared in `src/api/common/identity` and applied by itself, so a missing grant is measured by dispatching every workflow and fixed forward; the trust names GitHub's immutable subject, `DescribeLogGroups` is evaluated against `log-group::log-stream:`, and the OIDC provider is read by ARN

### Memories

- [a-memory-line-never-opens-with-an-issue-number](a-memory-line-never-opens-with-an-issue-number.md) — markdownlint reads a line opening with `#N` as a heading missing its space, so wrap a memory until no line starts with a hash

### Storage

- [the-store-holds-only-what-the-product-writes](the-store-holds-only-what-the-product-writes.md) — the store bucket has no working area, so a new prefix joins `_KEPT_BY_PREFIX` in the same commit as its writer or the next seed's prune deletes it; versioning is suspended, so every delete names `VersionId="null"` or leaves a marker the prune has to clear

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

- [a-chosen-carrier-pop-is-a-wan-pop](a-chosen-carrier-pop-is-a-wan-pop.md) — a carrier PoP the synthesis chooses is a `wan_pop`, `backbone` survives only where it names the mesh or the tier, `node` only in a flow network and an `ast` walk, and the five published resources the rename moved
- [a-site-is-a-named-place-not-a-building](a-site-is-a-named-place-not-a-building.md) — a site is a named place with a coordinate and nothing smaller is modelled, so no building exists here, the vertex the directive is proved over is a city, and the word to reach for instead of `building`
- [a-way-out-of-a-site-is-a-circuit](a-way-out-of-a-site-is-a-circuit.md) — a way out of a site is a circuit, its route is the carrier PoPs it runs through, `path` survives only for files on disk and two graph walks, and ordering and cost are outside the vocabulary
- [a-circuit-is-owned-one-segment-at-a-time](a-circuit-is-owned-one-segment-at-a-time.md) — a fiber segment is one carrier's when it has a PoP at both ends and a circuit hands off between carriers at any PoP both have; the synthesizer works over the merged fiber for that reason, and a one-carrier-per-circuit rule is never restated
