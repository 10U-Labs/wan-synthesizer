---
name: file-an-issue-where-it-belongs
description: A finding is filed in the repository that owns the code or the AWS resource it concerns; since the API migration a finding about the synthesizer or a served route belongs in api.10ulabs.com
metadata:
  type: feedback
---

# File an issue where it belongs

A finding is filed as an issue in the repository that owns the code or the AWS
resource it concerns, not filed here and not left as a note in an issue here.
Find the owner from the resource's `Repository` tag or from where the code
lives. Since the API migration, the synthesizer, its solver and every served
route live in `10U-Labs/api.10ulabs.com`, so a finding about any of them belongs
there; this repository keeps the data, the ETLs that load it, the SPA and the
deploy role.

**Why:** on 2026-10-07 in `10ulabs.com` an analysis traced a cost to the
`api.10ulabs.com` distribution and only said a fix belonged in that repository,
which left the user unsure whether anything had been filed. The user held that
an issue is filed where it belongs. Adopted here on 2026-10-07 under issue #255.
It is the filing-side counterpart of
[an-issue-follows-its-code-across-repositories](an-issue-follows-its-code-across-repositories.md),
which moves an issue already filed.

**How to apply:** write the issue from what this session can see, create any
label it needs in the target first, and link it from the issue that found it, as
`10U-Labs/api.10ulabs.com#N`. Filing waits on the user's go-ahead when the
finding came from an analysis
([an-analysis-issue-asks-for-analysis-only](an-analysis-issue-asks-for-analysis-only.md)).
