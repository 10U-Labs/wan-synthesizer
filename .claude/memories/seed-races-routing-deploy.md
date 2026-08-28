# Seed races the routing deploy

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Two workflows to wait for, and the status code says which](#two-workflows-to-wait-for-and-the-status-code-says-which)
  - [Wait for the route, then rerun the failed job](#wait-for-the-route-then-rerun-the-failed-job)

## Overview

Adding a new per-tenant store resource — a new `/tenants/{tenant}/<resource>` path in `openapi.json` plus a `seed.py` PUT — can fail the `seeding` job of `seed.yml` on the first push to `main`, while every existing resource PUTs fine. It is a deploy-ordering race, not a code defect: `seed`, `api_common_routing` and `api_endpoint_tenants` are independent path-filtered workflows on the same push, so `seed` can reach the live API before the new route and its handler exist.

## Conventions

### Two workflows to wait for, and the status code says which

A new resource needs the route (`api_common_routing`) *and* the tenants handler that stores it (`api_endpoint_tenants`, whose `_INPUTS` lists the collections it will accept). A missing route answers `HTTP 403 Forbidden`, since API Gateway rejects a path it does not define; a route whose handler has not caught up answers `HTTP 404 Not Found`, since the request reaches the old Lambda and it does not know the collection.

### Wait for the route, then rerun the failed job

Wait for both workflows to succeed, then re-run the failed seed job with `gh run rerun <run-id> --failed`; it passes on the second attempt. Do this explicitly rather than waiting for the next commit to cover it — a later commit that does not touch `etc/`, `openapi.json` or `seed.py` will not re-trigger `seed` at all, and the run stays red.
