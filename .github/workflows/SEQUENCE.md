# SEQUENCE

Dependency order across `src/` — identity, common infra, endpoints, and HTTP
actions. Each node is one workflow (`api_common_*`, `api_endpoint_*`). `A ─→ B`
means B builds on A: every workflow assumes the role `api/common/identity`
declares, so that stack sits ahead of every other and each reconciliation runs
under the permissions it enumerates; every endpoint reads the common `storage`
+ `routing` state. The synthesizer and the runs moved to `api.10ulabs.com`.

```text
api/common/identity ─┬─→ api/common/storage ─┐
                     └─→ api/common/routing ─┤
                                             ├─→ api/endpoints/carriers
                                             └─→ api/endpoints/providers
```
