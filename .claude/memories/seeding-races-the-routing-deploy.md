---
name: seeding-races-the-routing-deploy
description: seed can beat the deploy of anything it exercises: a new store resource fails the PUT with 403 or 404, and a synthesizer change fails nothing at all and grades WANs the old Lambda built
metadata:
  type: project
---

# Seeding races the routing deploy

Adding a new per-tenant store resource can fail the first `seed` run on the new PUT: `seed`, `api_common_routing` and `api_endpoint_tenants` are independent workflows on the same push, so seeding can beat both the route and the handler that stores it. The code says which is behind — `HTTP 403` is a route API Gateway does not define yet, `HTTP 404` is the old handler not knowing the collection. Wait for both, then `gh run rerun <run-id> --failed`. A later commit that misses `etc/`, `openapi.json` and `seed.py` will not re-trigger `seed` at all.

## A synthesizer change is graded before it is deployed

The same race with no error to read. `seed`'s `seeding` job POSTs a build for every tenant, and `reconciliation` in `api_endpoint_tenants_wan_post` is the terraform apply that ships the synthesizer Lambda. On one push `seeding` ran at 04:01:11 and `reconciliation` finished at 04:02:39, so all seven tenants were rebuilt on the old code and `e2e-tests` graded those. Nothing 403s or 404s: the run fails on whatever it was already failing on, or passes, and the figures come back byte-identical to the previous run. That repetition is the only tell.

`gh run rerun <run-id> --failed` is the wrong fix here and quietly gives the wrong answer, because `e2e-tests` is the only failed job and re-running it grades the same stale WANs. Wait for `reconciliation`, then re-run the whole workflow with `gh run rerun <run-id>` so `seeding` POSTs the builds again.

GitHub Actions orders nothing between workflows started by the same push, which is the same fact that puts the shared modules in a job inside each workflow rather than a workflow of their own: [shared-modules-are-tested-first](shared-modules-are-tested-first.md). What `seed.yml` runs before it reaches the live API is [seed-tests-every-push](seed-tests-every-push.md).
