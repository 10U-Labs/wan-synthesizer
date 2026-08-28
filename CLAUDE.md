# Working in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
    - [Every check is its own job](#every-check-is-its-own-job)
    - [Seeding races the routing deploy](#seeding-races-the-routing-deploy)
    - [Seeding tests every push](#seeding-tests-every-push)
    - [Shared modules are tested first](#shared-modules-are-tested-first)
    - [Where a test runs follows what starts it](#where-a-test-runs-follows-what-starts-it)
  - [Commits](#commits)
    - [A rejected push is fixed forward](#a-rejected-push-is-fixed-forward)
    - [Commit straight to main](#commit-straight-to-main)
  - [Issues](#issues)
    - [A blocked_by edge says one thing](#a-blocked_by-edge-says-one-thing)
    - [A finding is filed, not mentioned](#a-finding-is-filed-not-mentioned)
    - [An issue has six sections in a fixed order](#an-issue-has-six-sections-in-a-fixed-order)
    - [An issue states one solution](#an-issue-states-one-solution)
    - [Which issues owe the four test sections](#which-issues-owe-the-four-test-sections)
  - [Markdown](#markdown)
  - [Tests](#tests)
    - [Read the test tenets first](#read-the-test-tenets-first)
    - [Tenets are generic](#tenets-are-generic)
    - [The test tree splits on deployment phase](#the-test-tree-splits-on-deployment-phase)
    - [Write the test first](#write-the-test-first)
  - [Third-party code](#third-party-code)
  - [Verification](#verification)
    - [CI is the source of truth](#ci-is-the-source-of-truth)
    - [Find a run by the full hash](#find-a-run-by-the-full-hash)
  - [Writing](#writing)
    - [Code names say what the thing is](#code-names-say-what-the-thing-is)
    - [Lead with what it is for](#lead-with-what-it-is-for)
    - [Say peers and circuits](#say-peers-and-circuits)
    - [Say shorter, not cheaper](#say-shorter-not-cheaper)
    - [The code is the only explanation](#the-code-is-the-only-explanation)
    - [Write the exact name](#write-the-exact-name)
- [Notes](#notes)

## Overview

These are the standing conventions for working in this repository. Each section links the longer write-up behind it, one note per topic under `.claude/memories/`; [.claude/memories/README.md](.claude/memories/README.md) indexes them all.

## Conventions

### CI workflows

Longer:
[every-check-is-its-own-job](.claude/memories/every-check-is-its-own-job.md),
[shared-modules-are-tested-first](.claude/memories/shared-modules-are-tested-first.md),
[where-a-test-runs-follows-what-starts-it](.claude/memories/where-a-test-runs-follows-what-starts-it.md),
[seed-races-routing-deploy](.claude/memories/seed-races-routing-deploy.md),
[seed-tests-every-push](.claude/memories/seed-tests-every-push.md).

#### Every check is its own job

Every static-analysis check is a job of its own, so one push reports every finding it has instead of the first one. In every `api_*.yml` workflow the eleven checks are `lint-yaml`, `assert-no-inline-directives`, `assert-no-linter-config-files`, `assert-one-assert-per-pytest`, `pylint-source`, `mypy-source`, `copy-paste-source`, `pylint-tests`, `mypy-tests`, `copy-paste-tests` and `validate-stack`. `seed.yml` has eleven of its own: no `validate-stack`, since it deploys no OpenTofu, and no `lint-yaml`, its own `yamllint` job linting `.github/workflows/seed.yml` along with the seven tenant configs in `etc/`. They all start when the workflow does, they install only the tools they run, and they sit in alphabetical order in the file because `yamllint` runs with `key-ordering: enable`. `test-repo-libraries` starts with them rather than behind them. `reconciliation` — `seeding` in `seed.yml` — needs every gate in the workflow, because it runs `tofu apply` against live AWS and an apply cannot be taken back. A green tier beside a red check is unestablished rather than a pass.

#### Seeding races the routing deploy

Adding a new per-tenant store resource can fail the first `seed` run on the new PUT: `seed`, `api_common_routing` and `api_endpoint_tenants` are independent workflows on the same push, so seeding can beat both the route and the handler that stores it. The code says which is behind — `HTTP 403` is a route API Gateway does not define yet, `HTTP 404` is the old handler not knowing the collection. Wait for both, then `gh run rerun <run-id> --failed`. A later commit that misses `etc/`, `openapi.json` and `seed.py` will not re-trigger `seed` at all.

#### Seeding tests every push

Every push that starts `seed.yml` runs every tier, so no run reports success without testing the code that seeds. `unit-tests` and `integration-tests` carry `needs: test-repo-libraries` and no `if` at all, and `seeding` names all fifteen gates in one flat `and` beside `github.ref == 'refs/heads/main'` — every job in the workflow but itself and the `e2e-tests` that follows it. `test_seeding_waits_for_every_check_the_workflow_runs` and `test_seeding_demands_a_success_from_every_check_it_waits_for` in `test/scripts/seed/pre_deployment/integration/test_contracts.py` fail when a job is missing from either place. A skip cascades transitively to every descendant and an ordinary expression `if` does not break it, so a job under one that can skip needs its own status-check function, normally `if: ${{ !cancelled() && needs.<parent>.result == 'success' }}` — which is what `e2e-tests` carries against a `seeding` that skips off `main`.

#### Shared modules are tested first

Shared machinery is tested in every workflow that imports it, and before the tests that stand on it. A module under `lib/python/` has no workflow of its own and no single consumer, so its subtree under `test/lib/python/` runs in each workflow whose own tests import it, transitively. Each workflow that runs Python tests carries a `test-repo-libraries` job for this: it starts when the workflow does, runs all nine modules' tests rather than the subset that workflow imports, and is named in the `needs:` of every job there whose tests import them, written out rather than left to arrive down the chain. It gates each module with a `--cov=lib/python/<module>` of its own, so a module arriving without tests fails rather than being carried by its neighbours' numbers, and each workflow lists `test/lib/python/**` in its `paths`. A workflow of its own for these modules cannot be made to work, because GitHub Actions orders nothing between workflows started by the same push.

#### Where a test runs follows what starts it

A test runs in the workflow the change it guards arrives on. Tests about how an API behaves and how its deployment is shaped belong in that endpoint's own workflow. Whether a WAN was actually rebuilt from a change to `etc/` belongs in `seed.yml`, because a push touching `etc/` alone starts `seed.yml` and nothing else, and its `seeding` job is what delivers the change and POSTs the builds. Which directory a test sits in is the separate question of what it checks, and the two agreeing is the ordinary case; where they do not, the workflow must list the file and its whole conftest chain in its `paths`.

### Commits

Longer:
[commit-straight-to-main](.claude/memories/commit-straight-to-main.md),
[a-rejected-push-is-fixed-forward](.claude/memories/a-rejected-push-is-fixed-forward.md).

#### A rejected push is fixed forward

A push rejected by CI is answered with a follow-up commit. Do not amend and force-push: `main` is published by the time the run reports, and rewriting it discards what was tried. Where this collides with solving an issue in a single push, verifying only in CI is the rule that holds and the extra commits are its cost — local linting has been proposed and declined. Read the whole failed log rather than its first error, and sweep the change for other instances of the same shape before pushing the fix.

#### Commit straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. There is no pull-request buffer, so CI is the only review there is and the tests land in the same commit as the code they cover.

### Issues

Longer:
[how-issues-are-written](.claude/memories/how-issues-are-written.md),
[a-finding-is-filed-not-mentioned](.claude/memories/a-finding-is-filed-not-mentioned.md),
[an-issue-states-one-solution](.claude/memories/an-issue-states-one-solution.md).

#### A blocked_by edge says one thing

A `blocked_by` edge says one thing and only that thing: this issue cannot be finished until that one is. Add one when that is true of a pair and leave it off when it is not. Most issues are blocked by nothing and carry no edge, which is the ordinary case rather than an omission. The edges are not a running order and nothing reads them as one; which issue to pick up next is a judgement made from the open issues themselves. Add a real edge with `gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by -F issue_id=<id>`, where `<id>` is the numeric id from `gh api repos/{owner}/{repo}/issues/{n} --jq .id` and not the GraphQL node id, sent with `-F` and not `-f`.

#### A finding is filed, not mentioned

A defect noticed while doing something else is filed, not mentioned. Do not end a reply with "one more thing", "two other things I noticed" or "one thing I did not touch": a finding parked in a reply is lost the moment the session ends, nothing links it to the work, and the user is left holding a decision they have to remember to act on. File it in the six-section or two-section shape and then say in one line which number it is. Three cases are not this: something inside the scope of the task in hand is done rather than filed; a finding that reaches a genuine fork is asked about before filing; and a finding that cannot carry a "Problem" section saying what the defect costs is dropped rather than mentioned.

#### An issue has six sections in a fixed order

An issue about the program has six sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It", "Why Integration Tests Did Not Catch It", "Why E2E Tests Did Not Catch It", "Which Unit, Integration, or E2E regression tests would prevent this from happening again?", "Proposed Solution". Every such issue has all six; where a tier does not exist for the part of the program in question, saying so is the finding, not a reason to drop the section. The regression section names the tests to write, each with its tier and its assertion, and is separate from the solution so that a fix cannot ship with the coverage folded into its last paragraph. Write plain, ordinary English prose and use telecommunications vocabulary for the subject matter. Tables where a table genuinely reads better, bullets only when enumerating things, never to break up an argument. Back claims with numbers computed from the repository's own data, and say how they were computed. Each section opens with a plain sentence saying what the thing is and what it is for before any identifier appears; "Problem" says what the code is there to do before it says what is wrong with it, and says what the defect costs within its first few lines.

#### An issue states one solution

An issue is definitive. Its `Proposed Solution` names one change — this function, this file, this algorithm — because the issue is the instruction to whoever picks it up and they were not in the conversation that produced it. Never file "either X or Y", a menu with a recommendation, or a question left for the reader. Where a draft reaches a genuine fork, stop and ask which branch and then write down the branch that came back, so the asking happens before the filing rather than inside the body. Naming the rejected alternative and why it lost is still worth writing. For issues already on disk that carry an either, do not pick: ask which one before editing a file, however clearly the text leans toward one of them, and ask before there is a draft, because a draft turns the question into a request to approve what is already done.

#### Which issues owe the four test sections

The four test sections belong to the program and to nothing else. The program is what a test tier can run: `src/`, `lib/python/`, `scripts/`, and the OpenTofu under `lib/`. An issue about the configs in `etc/`, the PoPs and fiber segments in `data/`, the workflow files in `.github/workflows/` or the documentation has two sections, "Problem" and "Proposed Solution", and owes no tests — a test over a file no tier runs only reads a value back and asserts what it just read. `test/` falls on both sides: the machinery a tier runs on is program code and gets six, conftest fixtures included, because it can make a whole layer report the wrong answer and a unit tier can usually reach it; the assertions themselves get two, since asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.

### Markdown

Longer:
[markdown-is-not-hard-wrapped](.claude/memories/markdown-is-not-hard-wrapped.md).

Markdown is not hard-wrapped. There is no column limit on `.md` files here, and none on the bodies of GitHub issues and pull requests: write each paragraph as one line and let the reader wrap it. `markdownlint` runs with MD013 disabled and the YAML linters with `line-length: disable`, so no width is enforced anywhere. Most of the markdown already on disk was written wrapped before the restriction was lifted, so match this rule rather than the file next to you.

### Tests

Longer: [tdd-workflow](.claude/memories/tdd-workflow.md),
[read-test-tenets-first](.claude/memories/read-test-tenets-first.md),
[tenets-are-generic](.claude/memories/tenets-are-generic.md),
[the-test-tree-splits-on-deployment-phase](.claude/memories/the-test-tree-splits-on-deployment-phase.md).

#### Read the test tenets first

Read `docs/tenets/tests/` before implementing. Unit tests alone are not sufficient: add coverage at every tier the change touches, one assert per pytest.

#### Tenets are generic

Those docs are tenets, not a description of the suite. They name no language, tool, directory or resource, because the repository already states all of that and a second copy drifts. When a tenet and the repository disagree, the repository is what changes. Editing a tenet to match the code is backwards.

#### The test tree splits on deployment phase

Every subsystem under `test/` is laid out as `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}`, and a tier directory appears only when a test exists to put in it. The deployment phase is the top split because neither post-deployment tier can be attempted until there is a deployment to call. A journey against a localhost stub is pre-deployment integration however end-to-end it looks: `test/scripts/seed/pre_deployment/integration/test_cli.py` drives `scripts/seed.py` as a subprocess and touches nothing live, while `test/scripts/seed/post_deployment/e2e/test_delivered_syntheses.py` reads the deployed API.

#### Write the test first

We do TDD: the test is written first, then the code that makes it pass. Test-first means authoring order — the red and green observations belong to CI, since nothing runs locally.

### Third-party code

Longer:
[third-party-code-ships-as-a-layer](.claude/memories/third-party-code-ships-as-a-layer.md).

A package the synthesizer needs while it runs ships to AWS as a Lambda layer and is never unpacked into the code this repository publishes. The checks on a push exist to grade what the people here wrote, and a wheel unpacked under `src/` is graded too: `pylint-source`, `mypy-source` and `copy-paste-source` read the synthesizer's own directory, `data "archive_file" "synthesizer"` in `src/api/endpoints/tenants/wan/post/main.tf` zips the whole of that stack's `lambdas/` directory, and the findings that come back are answerable by nobody. `highspy` 1.15.1 and the `numpy` 2.3.5 it needs are pinned by version and by sha256, fetched and unpacked by the workflow before `tofu apply`, and shipped as `aws_lambda_layer_version.solver`, attached to both Lambdas in that stack. The next runtime dependency goes there the same way.

### Verification

Longer:
[verification-in-ci-only](.claude/memories/verification-in-ci-only.md),
[find-a-run-by-the-full-hash](.claude/memories/find-a-run-by-the-full-hash.md).

#### CI is the source of truth

CI is the source of truth. Do not run tests, linters or builds locally to verify a change — write the code and the tests, commit, push to `main`, and read the run with `gh run list` / `gh run watch` / `gh run view --log-failed`. Local runs cost tokens; CI is free and checks every gate at once. A push can trigger several path-filtered workflows. The change is done when each workflow that fired is green, not when the first one is.

#### Find a run by the full hash

Find the run by the full forty-character hash, from `git rev-parse HEAD`. `gh run list --commit` silently returns an empty list for the short hash `git log --oneline` prints, which is indistinguishable from a run that has not started, so anything that polls should instead list recent runs and match `headSha` by prefix locally.

### Writing

Longer:
[write-the-exact-name](.claude/memories/write-the-exact-name.md),
[lead-with-what-it-is-for](.claude/memories/lead-with-what-it-is-for.md),
[say-peers-and-circuits](.claude/memories/say-peers-and-circuits.md),
[code-names-say-what-the-thing-is](.claude/memories/code-names-say-what-the-thing-is.md),
[say-shorter-not-cheaper](.claude/memories/say-shorter-not-cheaper.md),
[the-code-is-the-only-explanation](.claude/memories/the-code-is-the-only-explanation.md).

#### Code names say what the thing is

A class, function, variable or field is named so that a reader meeting it for the first time can say what it holds or does, in ordinary words, without opening its definition. Name the thing the thing is, and avoid the filler nouns that attach to anything and so distinguish nothing: substrate, ground, context, handle, use, spec, info, data, manager, helper, wrapper. The list covers every name a reader meets, variables and parameters and fields as much as classes. Where the thing being named is a bundle of arguments rather than anything on the network, no name is the right answer, so a value built on one line and read on the next is deleted and built inside the call instead. Prefer the network engineer's word to the computer scientist's. Abbreviations only where the abbreviation is the ordinary form — `PoP`, `WAN` and `id` are, `cfg`, `res`, `idx` are not. This holds for new code as it is written and for old code as it is touched.

#### Lead with what it is for

Every paragraph opens with a plain sentence saying what the thing is and what it does, in words that need no file open, and the identifiers come after it — a name before that sentence is a demand, because the reader cannot yet tell why they are being told about it. Say what a defect costs in ordinary words near the top rather than in the seventh paragraph. Then cut: a detail stays where it changes what somebody would do and moves later or goes where it does not. Order for the reader, who has not opened the files and will not open them while reading, rather than for yourself, who knew the shape before writing a word. Explaining why a thing exists at all takes a shape of its own: say what the program is doing at that moment in one sentence, then what that step requires as a short list of facts, then the thing about those facts that forces the design, which is usually that some change and some do not. No analogies — say the PoPs, the fiber segments, the tenant's configuration and the miles. Short sentences, one fact each. Cutting a correct detail is not vagueness; replacing it with a coined noun is.

#### Say peers and circuits

Say peers and circuits. A peer is another backbone node this one has a circuit to; a circuit is one way from one site to another, crossing whatever cities the fiber makes it cross, and it is also the thing an operator orders and pays for every month. Those two words answer almost every question about a backbone, and each of them has one word only: not path, not route, not cable, not span, and not link. A synonym splits one thing into two. One length of fiber between two adjacent points is a fiber segment (`FiberSegment`); a city that every circuit out of a site crosses is a single point of failure, said in full rather than called a chokepoint. Say the word for the thing: a fiber segment, a circuit, an access circuit for a tenant site or provider region homing into its backbone node, and a forced or removed circuit for what an operator instructs; how many backbone nodes an access node homes into is a homing degree. Names a caller already sees keep their word until somebody deliberately changes the API: the published `backbone-links` collection, the `link_kind` field of each entry of the published `paths` collection, the four `ValidationReport` keys that spell link, and the `number_of_diverse_paths` key every tenant's `etc/*.yml` sets. Carrier PoPs, tenant sites, provider regions and off-net sites are all sites, and there are two kinds — a backbone node is seated in the backbone tier, an access node is a tenant site or provider region homing into it — and the sentence says which kind whenever it turns on the difference. Write "node" only as "backbone node" or "access node", never on its own. An identifier spelled with a banned word is wrong and gets renamed; until it is, write it exactly as it is spelled. What the synthesizer hands back is a synthesis, never a design: a solver computes it, and nobody sits down and draws it. Peers and diverse circuits are two different things and conflating them hides defects — `number_of_diverse_paths` is a requirement over the whole synthesis that `synthesizer.survivable.select_fiber` selects fiber to meet, a site's peers are what falls out of the circuits `synthesizer.backbone._ways_out_of` reads off that fiber, how many circuits one pair is drawn with is `synthesizer.ceiling.paths_per_peer`, and a site's diverse circuits are the circuits out of it no single city's loss takes two of.

#### Say shorter, not cheaper

Nothing here records money — no price, no tariff, no monthly charge, no currency in `src/`, `lib/`, `etc/` or `data/` — and every number the synthesizer compares or publishes is a distance in miles. "The cheapest circuit" claims a comparison of prices that never happened, and sends the reader looking for where the prices are configured. Say shorter, or the fewest fiber miles. That an operator pays for every circuit they hold is a fact about operators and is worth saying, because it is why an unneeded circuit is a defect; comparing two circuits by price is not, and a saving is stated in miles with the figure. `synthesizer.ceiling` is the exception that stays: its minimum-cost maximum flow measures cost in miles. Do not say "buy" either: the program **selects** fiber segments, so say selected, and say which decision is meant wherever a sentence could also mean the selected backbone nodes. Do not say a carrier "sells" fiber either: carriers offer fiber segments. What an operator does keeps its own words: they order a circuit from one carrier and pay for it every month.

#### The code is the only explanation

There are no docstrings and no comments anywhere the people here write: not in `src/`, `lib/python/`, `scripts/` or `test/`, not in the `.tf` files or those under `.github/workflows/`, not in `src/www/spa/app.js`, and the `assert-no-comments` job fails the run when one appears. A name, a signature and the shape of a function are the whole of what a reader gets, so when they are not enough to say what a thing holds or does, the thing is named or shaped wrong rather than under-explained. Prose beside code is never checked, so it stops being true and nothing says when. The reasoning still gets written down, in the commit message, the issue and these notes, each of which is dated and attached to a change instead of sitting beside a line claiming to describe it forever. `src/www/spa/vendor/leaflet.js` keeps its comments, like the pinned wheels that ship as `aws_lambda_layer_version.solver`, because nobody here can answer for somebody else's code. Where two mechanisms answer the same question and only one of them is reachable, the unreachable one is deleted rather than documented.

#### Write the exact name

Name things by their names, everywhere — chat replies as much as issues, pull requests and commit messages. A name is something the reader can open: a path, a function, class, constant or field with the file it lives in, an S3 object key, a workflow file, a config key, an endpoint with its method. Coined collective nouns are the failure to avoid: "the layer", "the machinery", "the pipeline", "the store" read as repository vocabulary the reader is meant to recognise, so they go looking and find nothing. Say the directory, the module, the bucket, the object key instead. Simple English and precision are separate requirements and both are owed: short sentences and no computer-science jargon where a plain word will do, and the exact identifier rather than a description of it. Verify a name before writing it — a wrong name costs more than a vague one, because it sends the reader somewhere real and wrong. A line number is not a name and does not belong in prose, because the next commit moves it and nothing says when: it goes only in a `::error file=,line=::` annotation, which is generated against the commit being checked and read minutes later against that same commit.

## Notes

A convention learned in a session belongs in this repository: a paragraph in this file and a topic file under `.claude/memories/`, linked from both indexes. The session tool's local memory directory is one machine's unversioned files, and a rule kept in both places drifts with nothing to signal it. Keep there only what is true of that machine alone.
