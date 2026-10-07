---
name: an-analysis-issue-asks-for-analysis-only
description: When an issue asks for something to be analyzed, the body states the request, the results go in a comment, and nothing is filed or changed because of a finding until the user says to
metadata:
  type: feedback
---

# An analysis issue asks for analysis only

When an issue asks to analyze something, such as a bill, a design, a log or a published synthesis, its work is the analysis. The body states the request: what is to be analyzed, and that acting on a finding is a separate decision. The results go in a comment on the issue. No finding is turned into an issue of its own, and no code, workflow or infrastructure is changed because of one, until the user says to.

**Why:** on 2026-10-07 in `10ulabs.com` an issue asked for the last AWS invoice to be analyzed for savings. The session wrote up the analysis, filed a new issue for one saving it found and began pushing changes for it, and the user stopped it: the issue had asked for an analysis only. Adopted here on 2026-10-07 under issue #255.

**How to apply:** give the results in a comment on the issue and in the reply to the user, then ask whether to act on them, per [one-question-at-a-time](one-question-at-a-time.md). This is the one place results go in a comment; a decision still rewrites the issue ([a-decision-rewrites-the-issue](a-decision-rewrites-the-issue.md)).
