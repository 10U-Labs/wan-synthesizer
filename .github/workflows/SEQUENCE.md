# SEQUENCE

Dependency order across `src/` — identity and common infra. Each node is one
workflow (`api_common_*`). `A ─→ B` means B builds on A: every workflow assumes
the role `api/common/identity` declares, so that stack sits ahead of every other
and each reconciliation runs under the permissions it enumerates. The
synthesizer, the runs, the carriers and the providers moved to
`api.10ulabs.com`.

```text
api/common/identity ─┬─→ api/common/storage
                     └─→ api/common/routing
```
