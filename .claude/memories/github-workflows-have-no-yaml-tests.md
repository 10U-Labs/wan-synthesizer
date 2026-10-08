---
name: github-workflows-have-no-yaml-tests
description: "No test file reads a GitHub workflow's YAML to check how it is set up; the programs a workflow runs are what get tested"
metadata:
  type: feedback
---

# GitHub workflows have no YAML tests

No pytest file loads a file under `.github/workflows/` and asserts on its
triggers, jobs, `needs`, steps or inputs. A workflow is not given a test file of
its own, and a rule about how workflows are set up is not held by one. The
programs a workflow runs, such as an ETL under `src/etl/`, are what the test
tree tests.

**Why:** the user decided on 2026-10-07 that GitHub workflows should not have
test files testing their YAML. Six such files had grown up here, one beside each
workflow but `scripts.yml`, and three of them were near-copies whose
duplication was the subject of issue #267.

**How to apply:** do not write a workflow test when adding or changing a
workflow, and do not answer a workflow rule with one. A memory that says a
workflow's tests hold some rule is out of date and is corrected.
