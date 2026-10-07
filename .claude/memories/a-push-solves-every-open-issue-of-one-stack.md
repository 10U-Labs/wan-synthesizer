---
name: a-push-solves-every-open-issue-of-one-stack
description: A batch is every open issue whose fix lands in one workflow's stack, solved in the working tree and pushed as one commit with one Closes line per issue; lib/python, test/conftest.py, test/lib and .github/workflows go in a push of their own, as does a red-run fix
metadata:
  type: feedback
---

# A push solves every open issue of one stack

A batch is every open issue that shares one matter, and the matter bounds it, never a count. Two issues share a matter when their fixes land in the same workflow's stack. `scripts.yml` fires on all of `src/**`, `test/**` and `lib/python/**`, so a stack here is the set of paths one workflow fires on beside `scripts.yml`:

| Workflow | Stack |
| --- | --- |
| `etl_carriers.yml` | `data/pops/`, `data/fiber_segments/`, `src/etl/carriers/`, `test/etl/carriers/` |
| `etl_regions.yml` | `data/providers/`, `src/etl/regions/`, `test/etl/regions/` |
| `etl_syntheses.yml` | `etc/`, `data/tenants/`, `src/etl/syntheses/`, `test/etl/syntheses/` |
| `www_identity.yml` | `src/www/identity/`, `test/www/identity/` |
| `www_spa.yml` | `src/www/spa/`, `test/www/spa/` |
| `documentation.yml` | the Markdown outside `.claude/`, `test/documentation/` |

**Why:**

- **Traceable red runs.** A batch inside one stack fires one workflow beside `scripts.yml`, so a red run points at files the batch touched, however many issues it holds. A batch spanning stacks turns every failing job into a search through unrelated changes. What makes a batch too big to trace is the number of stacks it mixes, not the number of issues it holds, so a count would cap the wrong thing.
- **Waiting.** Each push waits out its runs, and nothing else happens while they run. A batch of n issues shares that wait n ways.
- **Shared reading.** Issues of one stack are fixed in the same program, the same tests and the same workflow, so the reading done for the first serves the rest.

The rule comes from `10ulabs.com` and `api.10ulabs.com`, and was adopted here on 2026-10-07 under issue #255, in place of the autopilot's one-issue-per-push reminder.

**How to apply:**

1. **Seed.** Take the issue the autopilot's selection names first.
2. **Gather.** Add every open issue of the seed's stack. Leave out every issue labelled `needs decision`, and bring each issue up to date before starting it. When an issue's stack cannot be told without investigating it, take it in; if its fix turns out to land elsewhere, it leaves the batch and seeds a later one.
3. **Solve.** Solve the issues one after another in the working tree, each one's tests written before its source ([write-the-test-first](write-the-test-first.md)), and commit nothing until the last is done. As each issue is finished, write its paragraph of the commit message into the scratchpad, so nothing depends on the context outlasting the batch. An issue that turns out to need a person's decision is labelled for one, per [a-written-plan-is-decided](a-written-plan-is-decided.md), and its edits and tests come out of the tree before the commit.
4. **Commit.** Commit once, to `main` ([commit-straight-to-main](commit-straight-to-main.md)), staging each path by name ([stage-each-path-by-name](stage-each-path-by-name.md)). The subject names the stack and what the batch does to it; the body gives each issue its own paragraph; the message ends with one `Closes #N` line per issue ([an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md)).
5. **Push and read the runs.** CI is the verification ([ci-is-the-source-of-truth](ci-is-the-source-of-truth.md)). When a run goes red, trace each failing job to the issue whose change it names and fix forward ([fixing-a-red-run](fixing-a-red-run.md)). Once every run is clean, confirm the issues closed ([confirming-a-push-closed-its-issues](confirming-a-push-closed-its-issues.md)).

Some changes go in a push of their own and are never batched:

- A change under a path that several workflows fire on or read: `lib/python/`, `test/conftest.py`, `test/lib/` or `.github/workflows/`. Such a change alters what verifies every stack, so its fallout would hide the batch's own results.
- The fix for a red run.
- A problem met outside the batch's stack, which the autopilot solves rather than files: it is fixed in a push of its own once the batch has landed.

A change under `.claude/`, such as a memory or a skill, can join any batch, since only the Markdown lint reads it.
