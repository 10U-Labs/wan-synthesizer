---
name: the-description-check-reads-only-identifiers
description: assert-description-identifiers-exist catches a served description that spells a snake_case identifier the tree no longer holds, and nothing catches one that names a retired field in prose
metadata:
  type: project
---

# The description check reads only identifiers

`assert-description-identifiers-exist` reads every `description` in
`src/www/api/openapi.json`, extracts the snake_case tokens of four
characters or more, and fails when one is named nowhere under `src/`,
`lib/python/`, `scripts/` or `etc/`. That is the whole of what it holds.
A description that names a retired field the way prose names one — "the
backup path multiple" for `max_backup_path_multiple`, the instance GitHub
issue #160 was written about — is not a candidate and passes.

**Why:** the job was asked for under a name that claimed the wider class,
and a green run was read as "no served description names something that
does not exist", which it has never meant; GitHub issue #182 is the
record. Widening the pattern to English words would refuse ordinary
sentences, and no rule tells "the backup path multiple" from "the
coverage it delivered", so the wider class has no job and is held by
reading.

**How to apply:** a commit that removes a served field opens
`openapi.json` and reads the descriptions of the routes that carried it,
green job or not. A description that names a property should spell its
identifier, which is the case the job does hold. The reason a job rather
than a tier holds the narrow class is
[why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md).
