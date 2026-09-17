# Notes for Claude sessions in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
  - [Comments](#comments)
  - [Commits](#commits)
  - [Issues](#issues)
  - [Login](#login)
  - [Identity](#identity)
  - [Memories](#memories)
  - [Tests](#tests)
  - [Verification](#verification)
  - [Vocabulary](#vocabulary)
  - [ETLs](#etls)

## Overview

This directory is the rulebook. One memory holds one rule, so a session can recall the one it needs without reading the rest, and each file carries the reasoning behind its rule rather than only the instruction. This index is read at the start of every session and the memories themselves are recalled by relevance, so each line below says enough to know whether the file behind it is the one to open. A convention learned in a session belongs here, as a new memory and a line in this index.

## Conventions

### CI workflows

- [shared-modules-are-tested-first](shared-modules-are-tested-first.md) — every `lib/python` module has a `test-lib-<module>` job in `scripts.yml` under a 100% coverage gate, its definitions are named outside its own tests, and a workflow whose program imports it lists `lib/python/**`
- [every-workflow-runs-the-assert-tools](every-workflow-runs-the-assert-tools.md) — the six `assert-*` tools `10ulabs.com` runs and this repository did not now run here, four per workflow beside `assert-one-assert-per-pytest`, the OpenTofu one per stack, fixture liveness over the whole tree in `scripts.yml`; a fixture takes a `name=` only where its file binds that name
- [aws-is-called-over-fips-endpoints](aws-is-called-over-fips-endpoints.md) — every role-assuming workflow's `env` sets `AWS_USE_FIPS_ENDPOINT` to `true`; nothing in the tree holds that since the API migration, so a new workflow copies the block
- [code-scanning-is-held-on-by-a-test](code-scanning-is-held-on-by-a-test.md) — CodeQL default setup runs the extended suite over the Python and the JavaScript, `test/documentation` holds a fresh analysis of each language and zero results on the newest through the API the workflow token can read, and an alert it raises is fixed in the session that sees it
- [where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md) — a test runs in the workflow the change it guards arrives on, and one that already runs in two needs no cross-listed `paths`

### Comments

- [the-code-is-the-only-explanation](the-code-is-the-only-explanation.md) — no docstrings and no comments anywhere the people here write; `assert-no-comments` fails the run when one appears

### Commits

- [commit-straight-to-main](commit-straight-to-main.md) — direct commits to `main`, no feature branch and no pull request
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a red run is answered with a follow-up commit, never an amend and force-push
- [push-over-ssh-not-https](push-over-ssh-not-https.md) — an HTTPS push carrying a workflow file is refused for want of the `workflow` scope, and the fix is the remote URL rather than the token
- [an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md) — a `Closes #N` line in the commit that solves it, one line per issue; naming an issue in prose references it without closing it
- [an-issue-whose-premise-is-false-is-closed-with-the-finding](an-issue-whose-premise-is-false-is-closed-with-the-finding.md) — a defect the code cannot produce is closed by a comment with the argument and the measurement, never by a behaviour-identical refactor whose test cannot go red
- [an-issue-follows-its-code-across-repositories](an-issue-follows-its-code-across-repositories.md) — an issue about code that moved to `api.10ulabs.com` is re-read against the code there and transferred with `gh issue transfer` if it still holds, or closed here with the finding if the move dissolved it; create any missing label there first, and read an issue through `gh api` since `gh issue view --comments` prints nothing

### Issues

- [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md) — a job refuses a shape everywhere at once where a tier catches one occurrence

### Login

- [the-spa-signs-in-with-a-google-account](the-spa-signs-in-with-a-google-account.md) — the map opens on a Google sign-in card for a `10ulabs.com` account, sends the ID token as a bearer to `api.10ulabs.com`, ends a session through one `endSession` on sign-out, at the token's `exp` or after 15 idle minutes, and is served with `10ulabs.com`'s security headers and its own `<meta>` CSP, each held by a unit or e2e test; the API side of the login lives in `api.10ulabs.com`

### Identity

- [the-state-bucket-admits-only-the-principals-that-write-state](the-state-bucket-admits-only-the-principals-that-write-state.md) — `10ulabs-terraform-state-us-east-2` lives in `10U-Labs/10ulabs.com`'s bootstrap, denies every principal but the account, the admin user and the two deploy roles, and versions every state for 90 days; a new state-writing role is admitted there, in the `Deny`'s exception list and never the `Allow`
- [the-deploy-role-is-narrowed-by-its-own-stack](the-deploy-role-is-narrowed-by-its-own-stack.md) — `TenULabsWanSynthesizerRole` is declared in `src/www/identity` and applied by itself with four inline policies and no managed one, so a missing grant is fixed forward in `iam.tf`; the trust names GitHub's immutable subject, the OIDC provider is read by ARN, and the `Api` policy is the one read of `/api.10ulabs.com/api-key` the ETLs need

### Memories

- [a-memory-line-never-opens-with-an-issue-number](a-memory-line-never-opens-with-an-issue-number.md) — markdownlint reads a line opening with `#N` as a heading missing its space, so wrap a memory until no line starts with a hash

### Tests

- [write-the-test-first](write-the-test-first.md) — the test is authored before the code, and red and green are observed in CI
- [cover-every-tier-the-change-touches](cover-every-tier-the-change-touches.md) — unit tests alone are not sufficient, one assert per pytest
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` under every subsystem

### Verification

- [ci-is-the-source-of-truth](ci-is-the-source-of-truth.md) — nothing is verified locally; the change is done when every workflow that fired is green
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, so match `headSha` by prefix locally

### Vocabulary

- [a-chosen-carrier-pop-is-a-wan-pop](a-chosen-carrier-pop-is-a-wan-pop.md) — a carrier PoP the synthesis chooses is a `wan_pop`, `backbone` survives only where it names the mesh or the tier, `node` only in a flow network and an `ast` walk, and the five published resources the rename moved
- [a-site-is-a-named-place-not-a-building](a-site-is-a-named-place-not-a-building.md) — a site is a tenant's named place with a coordinate and nothing smaller is modelled, so no building exists here; a carrier PoP is a PoP, a provider region is a region and an off-net row is an `Off-net PoP`, never a site; the vertex the directive is proved over is a city, and the word to reach for instead of `building`
- [a-way-out-is-a-circuit](a-way-out-is-a-circuit.md) — a way out of a site or a WAN PoP is a circuit, its route is the carrier PoPs it runs through, `path` survives only for files on disk and two graph walks, and ordering and cost are outside the vocabulary
- [the-over-water-rule-holds-one-hop-at-a-time](the-over-water-rule-holds-one-hop-at-a-time.md) — a crossing never arrives on the shore its hop started from, and that is all the rule says; a WAN spanning two shores is two-vertex-connected the long way round, so a floor row never asks a pair two circuits over land, and `SeparationQuestion.barred` is how a row bars an arc rather than a segment
- [a-circuit-is-owned-one-segment-at-a-time](a-circuit-is-owned-one-segment-at-a-time.md) — a fiber segment is one carrier's when it has a PoP at both ends and a circuit hands off between carriers at any PoP both have; the synthesizer works over the merged fiber for that reason, and a one-carrier-per-circuit rule is never restated

### ETLs

- [an-etl-is-a-program-beside-its-data](an-etl-is-a-program-beside-its-data.md) — a dataset under `data/` or `etc/` reaches `api.10ulabs.com` through one program under `src/etl/<dataset>/` that `etl_<dataset>.yml` invokes with the key from SSM, masked and in the environment; the program reads what changed off `git diff` since the last successful run, builds before it deletes, retries a throttled call, and polls the cached listing until it agrees before exiting
