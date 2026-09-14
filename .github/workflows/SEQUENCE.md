# SEQUENCE

Dependency order across `src/` — identity, common infra, endpoints, and HTTP
actions. Each node is one workflow (`api_common_*`, `api_endpoint_*`). `A ─→ B`
means B builds on A: every workflow assumes the role `api/common/identity`
declares, so that stack sits ahead of every other and each reconciliation runs
under the permissions it enumerates; every endpoint reads the common `storage`
+ `routing` state, and a carrier write cascades to its builder
(`carriers/merge`). The synthesizer moved to `api.10ulabs.com`, so
`tenants/wan` serves a run's status alone.

```text
api/common/identity ─┬─→ api/common/storage ─┐
                     └─→ api/common/routing ─┤
                                             ├─→ api/endpoints/carriers ─────→ api/endpoints/carriers/merge
                                             ├─→ api/endpoints/providers
                                             └─→ api/endpoints/tenants ──────→ api/endpoints/tenants/wan
```
