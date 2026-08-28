# Notes for Claude sessions in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
  - [Tests](#tests)
  - [Working practice](#working-practice)

## Overview

`CLAUDE.md` at the repository root carries the standing conventions in short form and is read at the start of every session. These files carry the longer versions: the reasoning behind each rule and the details needed occasionally rather than constantly. One note per topic, so a session can read the one rule it needs. A convention learned in a session belongs here — a paragraph in `CLAUDE.md` and a topic file in this directory, linked from both indexes. Keep in the session tool's local memory only what is true of one machine alone.

## Conventions

### CI workflows

- [seed-races-routing-deploy](seed-races-routing-deploy.md) — a new tenant resource can 403 in `seed` before `api_common_routing` publishes its route
- [seed-tests-every-push](seed-tests-every-push.md) — every push that starts `seed.yml` runs every tier
- [where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md) — a test runs in the workflow the change it guards arrives on
- [shared-modules-are-tested-first](shared-modules-are-tested-first.md) — `test-repo-libraries` runs every module's tests ahead of every job whose tests import them
- [every-check-is-its-own-job](every-check-is-its-own-job.md) — the static-analysis checks are jobs that start together, so one push reports every finding it has

### Tests

- [tdd-workflow](tdd-workflow.md) — the test is written before the code, in the same commit
- [read-test-tenets-first](read-test-tenets-first.md) — read `docs/tenets/tests/` before implementing, and cover every tier the change touches
- [tenets-are-generic](tenets-are-generic.md) — the tenets name no tool, language or directory; the repository follows them, not the reverse
- [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md) — `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}` in every subsystem

### Working practice

- [verification-in-ci-only](verification-in-ci-only.md) — nothing runs locally; push and read the run
- [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` returns nothing for a short hash, and says nothing about why
- [commit-straight-to-main](commit-straight-to-main.md) — direct commits, no branches and no pull requests
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — a failed run is answered with a follow-up commit, never an amended force-push
- [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md) — no column limit on `.md` files or on issue and pull-request bodies
- [third-party-code-ships-as-a-layer](third-party-code-ships-as-a-layer.md) — a package the synthesizer needs at runtime ships as a Lambda layer, never unpacked under `src/`
- [how-issues-are-written](how-issues-are-written.md) — six fixed sections for the program, two for everything else
- [write-the-exact-name](write-the-exact-name.md) — name the file, function and key everywhere; never a coined collective noun
- [lead-with-what-it-is-for](lead-with-what-it-is-for.md) — say what the thing is and what it costs before the first identifier
- [say-peers-and-circuits](say-peers-and-circuits.md) — one word per thing: circuit, peer, fiber segment, single point of failure, backbone node, access node
- [code-names-say-what-the-thing-is](code-names-say-what-the-thing-is.md) — a name says what the thing holds without opening it; no filler nouns
- [say-shorter-not-cheaper](say-shorter-not-cheaper.md) — the repository records miles and no money, so a circuit is shorter, never cheaper
- [the-code-is-the-only-explanation](the-code-is-the-only-explanation.md) — no docstrings and no comments; the reasoning goes in the commit message, the issue and these notes
- [an-issue-states-one-solution](an-issue-states-one-solution.md) — a `Proposed Solution` names one change; a fork is asked about before the issue is filed
- [a-finding-is-filed-not-mentioned](a-finding-is-filed-not-mentioned.md) — a defect noticed while doing something else is filed, never parked at the end of a reply
