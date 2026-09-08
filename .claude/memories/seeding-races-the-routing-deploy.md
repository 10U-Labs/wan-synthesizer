---
name: seeding-races-the-routing-deploy
description: The first seed run after a new per-tenant store resource can fail on the new PUT, because seed, the route and the handler are three workflows on one push
metadata:
  type: project
---

# Seeding races the routing deploy

Adding a new per-tenant store resource can fail the first `seed` run on the new PUT: `seed`, `api_common_routing` and `api_endpoint_tenants` are independent workflows on the same push, so seeding can beat both the route and the handler that stores it. The code says which is behind — `HTTP 403` is a route API Gateway does not define yet, `HTTP 404` is the old handler not knowing the collection. Wait for both, then `gh run rerun <run-id> --failed`. A later commit that misses `etc/`, `openapi.json` and `seed.py` will not re-trigger `seed` at all.

GitHub Actions orders nothing between workflows started by the same push, which is the same fact that puts the shared modules in a job inside each workflow rather than a workflow of their own: [[shared-modules-are-tested-first]]. What `seed.yml` runs before it reaches the live API is [[seed-tests-every-push]].
