# Notes for Claude sessions in wan-synthesizer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [CI workflows](#ci-workflows)
  - [Issues](#issues)
  - [Third-party code](#third-party-code)
  - [Writing](#writing)

## Overview

`CLAUDE.md` at the repository root carries the standing conventions in short form and is read at the start of every session. A note exists here only where it carries something `CLAUDE.md` cannot: the reasoning behind a rule, or the detail needed occasionally rather than constantly. A rule whose whole statement fits in `CLAUDE.md` has no note. One note per topic, so a session can read the one rule it needs. A convention learned in a session belongs here — a paragraph in `CLAUDE.md` and a topic file in this directory, linked from both indexes. Keep in the session tool's local memory only what is true of one machine alone.

## Conventions

### CI workflows

- [seed-tests-every-push](seed-tests-every-push.md) — every push that starts `seed.yml` runs every tier, and how a new check is wired in
- [shared-modules-are-tested-first](shared-modules-are-tested-first.md) — `test-repo-libraries` runs every module's tests ahead of every job whose tests import them
- [where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md) — a test runs in the workflow the change it guards arrives on

### Issues

- [how-issues-are-written](how-issues-are-written.md) — six fixed sections for the program, two for everything else
- [an-issue-states-one-solution](an-issue-states-one-solution.md) — a `Proposed Solution` names one change; a fork is asked about before the issue is filed
- [a-finding-is-filed-not-mentioned](a-finding-is-filed-not-mentioned.md) — a defect noticed while doing something else is filed, never parked at the end of a reply

### Third-party code

- [third-party-code-ships-as-a-layer](third-party-code-ships-as-a-layer.md) — a package the synthesizer needs at runtime ships as a Lambda layer, never unpacked under `src/`

### Writing

- [write-the-exact-name](write-the-exact-name.md) — name the file, function and key everywhere; never a coined collective noun
- [say-peers-and-circuits](say-peers-and-circuits.md) — one word per thing: circuit, peer, fiber segment, single point of failure, backbone node, access node
- [code-names-say-what-the-thing-is](code-names-say-what-the-thing-is.md) — a name says what the thing holds without opening it; no filler nouns
- [say-shorter-not-cheaper](say-shorter-not-cheaper.md) — the repository records miles and no money, so a circuit is shorter, never cheaper
- [the-code-is-the-only-explanation](the-code-is-the-only-explanation.md) — no docstrings and no comments; the reasoning goes in the commit message, the issue and these notes
