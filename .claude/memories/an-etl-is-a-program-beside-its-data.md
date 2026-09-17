---
name: an-etl-is-a-program-beside-its-data
description: "A dataset under data/ or etc/ is carried into api.10ulabs.com by one program under src/etl/<dataset>/ that a workflow etl_<dataset>.yml invokes with the key from SSM; the program decides what changed since the last successful run, builds before it deletes, retries a throttled call, and ends only when the cached listing agrees with what it wrote"
metadata: 
  node_type: memory
  type: project
  originSessionId: 474dda51-b794-4803-bc4a-419291a3824c
  modified: 2026-09-17T13:25:10.609Z
---

# An ETL is a program beside its data

Since 2026-09-17 (GitHub issue #248, `b090312c`) `data/pops` and
`data/fiber_segments` reach `api.10ulabs.com` through
`src/etl/carriers/load_carriers.py`, which `etl_carriers.yml` invokes
as `python3 -c 'from etl.carriers import load_carriers; ...main(...)'`
with `PYTHONPATH=src:lib/python`. `api.10ulabs.com` serves routes and
loads nothing ([[the-store-holds-only-what-the-product-writes]] is the
old store; the API's memory `this-repo-serves-routes-and-loads-nothing`
is the other half of this rule).

**Why:** the loading job that used to sit in the API's own workflow
made the repository that creates REST APIs the keeper of the CSVs and a
writer to its own live API on every push. The data lives here, so the
one tool that carries it lives here, one per dataset.

**How to apply:**

- The workflow hands the program the key alone: `aws ssm get-parameter
  --name /api.10ulabs.com/api-key --with-decryption`, `::add-mask::`,
  then `API_KEY=` in the environment, never an argument. The grant is
  the `Api` policy of `src/www/identity` (GitHub issue #247).
- The program takes what to load three ways: named (`--carrier`), read
  off `git diff --since <sha> HEAD` over its data paths (the workflow
  passes the head of its own last successful run, falling back to
  `github.event.before`; the null sha means everything), or everything
  when neither is given. A `workflow_dispatch` input `all` forces
  everything. The checkout needs `fetch-depth: 0` for the diff.
- A member is built new before its stale copies are deleted, so a
  failure between the two leaves the old copy whole beside a partial
  one that the next run deletes; a member whose files are gone is
  deleted and not built. `DELETE` answering 404 is tolerated.
- 429, 502, 503 and 504 are tried again after a growing pause; 502 is
  what the gateway answers when a handler runs past its timeout.
- `GET` listings are served from a CloudFront cache the writes
  invalidate asynchronously, so the program polls the listing until it
  agrees with what it wrote (`--settle-seconds`, 300 by default) and
  exits 1 if it never does. A post-deployment tier can then read once.
- The pre-deployment integration tier drives `main()` in process
  against a fake of the verbs (`conftest.py` beside the tests), with
  `time.sleep` injected so the retry and settle pauses are recorded
  rather than slept; the post-deployment e2e tier reads every member
  back from the live API and holds it to its CSVs. The workflow copies
  the pytest jobs of `www_spa.yml` and gates coverage of the program
  at 100%.
- The runner's system `botocore` is old and calls `utcnow()`, so a job
  that runs boto3 under `--pythonwarnings=error` does `pip install
  --upgrade boto3`.
- A wait for CI longer than a minute runs in the background (`sleep`
  loops in a `run_in_background` shell), so the autopilot reminders
  keep firing; the API's memory `a-wait-runs-in-the-background` says
  the same.

Related: [[write-the-test-first]], [[cover-every-tier-the-change-touches]],
[[where-a-test-runs-follows-what-starts-it]].
