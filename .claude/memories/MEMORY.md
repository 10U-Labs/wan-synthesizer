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
  - [Sessions](#sessions)
  - [Infrastructure](#infrastructure)
  - [Working with the user](#working-with-the-user)
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
- [a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md) — a batch is every open issue of one workflow's stack, solved in the tree and pushed as one commit with one `Closes #N` line each; `lib/python`, `test/conftest.py`, `test/lib`, `.github/workflows` and a red-run fix go alone
- [stage-each-path-by-name](stage-each-path-by-name.md) — never `git add -A`; removals on `git rm`, since one missing pathspec makes `git add` stage nothing, and `git status --porcelain` before committing
- [no-ci-skip-in-commit-messages](no-ci-skip-in-commit-messages.md) — the `paths` filters decide what runs, and a skipped run verifies nothing
- [confirming-a-push-closed-its-issues](confirming-a-push-closed-its-issues.md) — GitHub can land a commit without acting on its `Closes` lines, so check each issue once the runs are clean
- [a-revert-does-not-reopen](a-revert-does-not-reopen.md) — reverting the commit that closed an issue leaves it closed, so reopen it by hand
- [an-issue-follows-its-code-across-repositories](an-issue-follows-its-code-across-repositories.md) — an issue about code that moved to `api.10ulabs.com` is re-read against the code there and transferred with `gh issue transfer` if it still holds, or closed here with the finding if the move dissolved it; create any missing label there first, and read an issue through `gh api` since `gh issue view --comments` prints nothing

### Issues

- [an-issue-is-split-by-problem-not-by-fix](an-issue-is-split-by-problem-not-by-fix.md) — one indivisible problem per issue, never merged to cut the count; batches bring issues together
- [a-written-plan-is-decided](a-written-plan-is-decided.md) — `needs decision` only for a choice the directive, the memories, the issue and the code leave open; a plan the issue states is decided
- [a-decision-rewrites-the-issue](a-decision-rewrites-the-issue.md) — a person's decision goes into the title and body and the label comes off, never a comment
- [issues-have-no-house-style](issues-have-no-house-style.md) — no fixed sections; a part of the body takes a `##` heading, never a bold lead sentence
- [issues-define-their-terms](issues-define-their-terms.md) — written for a reader who opens it from the list, each name and figure tied to the problem
- [issues-state-conclusions-not-the-trail](issues-state-conclusions-not-the-trail.md) — a settled question is rewritten as its answer, and the options it ruled out are cut
- [solving-what-a-session-finds](solving-what-a-session-finds.md) — file what a session finds, one problem per issue, and solve one now only if the work in hand cannot move forward without it
- [what-does-not-get-filed](what-does-not-get-filed.md) — a defect the commit fixes is stated in it, and one an open issue covers is cited
- [research-lives-in-issues](research-lives-in-issues.md) — a plan of discovery that outlasts the session is filed as it goes, with its method
- [an-analysis-issue-asks-for-analysis-only](an-analysis-issue-asks-for-analysis-only.md) — results in a comment, and nothing filed or changed on a finding without a go-ahead
- [code-is-changed-only-in-this-repository](code-is-changed-only-in-this-repository.md) — no edit, commit or push in another repository and no reading its runs; an issue can be filed or transferred there
- [file-an-issue-where-it-belongs](file-an-issue-where-it-belongs.md) — in the repository that owns the code or resource, which for the synthesizer and its routes is `api.10ulabs.com`
- [no-wrapping-outside-md-files](no-wrapping-outside-md-files.md) — an issue body or comment has one line per paragraph
- [a-new-check-is-its-own-assert-repository](a-new-check-is-its-own-assert-repository.md) — a rule nothing checks is answered by a new `assert-*` repository cloned from the newest, which a person creates
- [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md) — a job refuses a shape everywhere at once where a tier catches one occurrence

### Login

- [the-spa-signs-in-with-a-google-account](the-spa-signs-in-with-a-google-account.md) — the map opens on a Google sign-in card for a `10ulabs.com` account, sends the ID token as a bearer to `api.10ulabs.com`, ends a session through one `endSession` on sign-out, at the token's `exp` or after 15 idle minutes, and is served with `10ulabs.com`'s security headers and its own `<meta>` CSP, each held by a unit or e2e test; the API side of the login lives in `api.10ulabs.com`

### Identity

- [the-state-bucket-admits-only-the-principals-that-write-state](the-state-bucket-admits-only-the-principals-that-write-state.md) — `10ulabs-terraform-state-us-east-2` lives in `10U-Labs/10ulabs.com`'s bootstrap, denies every principal but the account, the admin user and the two deploy roles, and versions every state for 90 days; a new state-writing role is admitted there, in the `Deny`'s exception list and never the `Allow`
- [the-deploy-role-is-narrowed-by-its-own-stack](the-deploy-role-is-narrowed-by-its-own-stack.md) — `TenULabsWanSynthesizerRole` is declared in `src/www/identity` and applied by itself with four inline policies and no managed one, so a missing grant is fixed forward in `iam.tf`; the trust names GitHub's immutable subject, the OIDC provider is read by ARN, and the `Api` policy is the one read of `/api.10ulabs.com/api-key` the ETLs need

### Memories

- [a-memory-links-with-a-markdown-link](a-memory-links-with-a-markdown-link.md) — `[name](name.md)`, never `[[name]]`, whatever the session tool's default says
- [a-memory-line-never-opens-with-an-issue-number](a-memory-line-never-opens-with-an-issue-number.md) — markdownlint reads a line opening with `#N` as a heading missing its space, so wrap a memory until no line starts with a hash

### Tests

- [write-the-test-first](write-the-test-first.md) — the test is authored before the code, a file not yet written is read in a fixture with no default or skip, and red and green are observed in CI
- [cover-every-tier-the-change-touches](cover-every-tier-the-change-touches.md) — unit tests alone are not sufficient, one assert per pytest
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` under every subsystem
- [discriminating-test-inputs](discriminating-test-inputs.md) — choose literals so wrong code gives a different answer
- [a-raise-expected-in-a-test-is-raised-in-a-fixture](a-raise-expected-in-a-test-is-raised-in-a-fixture.md) — `pytest.raises` counts as an assert, so the raising call goes in a fixture
- [fixture-liveness-is-a-collection-question](fixture-liveness-is-a-collection-question.md) — never call a fixture dead from a grep; `assert-pytest-fixture-is-requested` answers it
- [share-code-a-change-mirrors](share-code-a-change-mirrors.md) — the jscpd jobs run at threshold 0, so two bodies a change makes equal are shared before pushing
- [pylint-refactor-messages-are-hard-failures](pylint-refactor-messages-are-hard-failures.md) — `--fail-on=C,R,W` makes the default argument, local, branch and statement limits hard, and the way out is to split

### Verification

- [ci-is-the-source-of-truth](ci-is-the-source-of-truth.md) — nothing is verified locally; the change is done when every workflow that fired is green
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, so match `headSha` by prefix locally
- [a-wait-runs-in-the-background](a-wait-runs-in-the-background.md) — a CI wait is a background call or a `Monitor`, never a foreground `sleep` or `gh run watch`, so the reminders keep firing
- [push-once-and-let-the-run-finish](push-once-and-let-the-run-finish.md) — four workflows cancel an in-progress run on the next push and the ETLs queue, so check `gh run list --limit 1` first and read a run only once it completes
- [fixing-a-red-run](fixing-a-red-run.md) — the session whose push went red fixes it, caused or inherited, in a push of its own before the next batch
- [a-fix-touches-only-what-must-be-fixed](a-fix-touches-only-what-must-be-fixed.md) — no edit only to make a workflow run
- [a-failure-outside-the-code-is-re-run](a-failure-outside-the-code-is-re-run.md) — a download or registry failure is `gh run rerun --failed` on the same commit, not a new commit

### Sessions

- [long-running-commands-in-the-background](long-running-commands-in-the-background.md) — anything past a minute runs in the background with a time limit and its output in the scratchpad, never followed by a foreground wait
- [every-task-is-indivisible](every-task-is-indivisible.md) — a task on the list names one action, counted from its subject rather than its purpose, and is split before work starts
- [writing-code-in-the-main-session](writing-code-in-the-main-session.md) — the reminders reach only the main session, so subagents do read-only searches and nothing else

### Infrastructure

- [a-renamed-label-is-moved-in-state](a-renamed-label-is-moved-in-state.md) — a relabelled OpenTofu resource carries a `moved` block, or tofu destroys it first, and here that can be the role the apply runs as
- [check-directly-not-by-a-daily-metric](check-directly-not-by-a-daily-metric.md) — confirm AWS work by querying the resource, never by waiting on a once-a-day metric

### Working with the user

- [one-question-at-a-time](one-question-at-a-time.md) — one plain question per message with a recommendation; when the user is lost, start from the smallest concrete example
- [do-not-offer-a-pointless-choice](do-not-offer-a-pointless-choice.md) — where the options differ in nothing the user cares about, pick one
- [never-quote-the-user-verbatim](never-quote-the-user-verbatim.md) — paraphrase the user everywhere, memories and issues included
- [check-before-claiming](check-before-claiming.md) — ask `gh api` before saying GitHub cannot, and read a tool before writing what it does
- [report-times-in-local-time](report-times-in-local-time.md) — US Eastern as `date` prints it, never UTC
- [progress-reports-are-tables](progress-reports-are-tables.md) — one value per column, the same columns each time

### Vocabulary

- [a-chosen-carrier-pop-is-a-wan-pop](a-chosen-carrier-pop-is-a-wan-pop.md) — a carrier PoP the synthesis chooses is a `wan_pop`, `backbone` survives only where it names the mesh or the tier, and `node` only in a flow network and an `ast` walk
- [a-site-is-a-named-place-not-a-building](a-site-is-a-named-place-not-a-building.md) — a site is a tenant's named place with a coordinate and nothing smaller is modelled, so no building exists here; a carrier PoP is a PoP, a provider region is a region and an off-net row is an `Off-net PoP`, never a site; the vertex the directive is proved over is a city, and the word to reach for instead of `building`
- [a-way-out-is-a-circuit](a-way-out-is-a-circuit.md) — a way out of a site or a WAN PoP is a circuit, its route is the carrier PoPs it runs through, `path` survives only for files on disk and two graph walks, and ordering and cost are outside the vocabulary
- [the-over-water-rule-holds-one-hop-at-a-time](the-over-water-rule-holds-one-hop-at-a-time.md) — a crossing never arrives on the shore its hop started from, and that is all the rule says; a WAN spanning two shores is two-vertex-connected the long way round, so a floor row never asks a pair two circuits over land, and `SeparationQuestion.barred` is how a row bars an arc rather than a segment
- [a-circuit-is-owned-one-segment-at-a-time](a-circuit-is-owned-one-segment-at-a-time.md) — a fiber segment is one carrier's when it has a PoP at both ends and a circuit hands off between carriers at any PoP both have; the synthesizer works over the merged fiber for that reason, and a one-carrier-per-circuit rule is never restated

### ETLs

- [an-etl-is-a-program-beside-its-data](an-etl-is-a-program-beside-its-data.md) — a dataset under `data/` or `etc/` reaches `api.10ulabs.com` through one program under `src/etl/<dataset>/` that `etl_<dataset>.yml` invokes with the key from SSM, masked and in the environment; the program reads what changed off `git diff` since the last successful run, builds before it deletes, retries a throttled call, and polls the cached listing until it agrees before exiting
