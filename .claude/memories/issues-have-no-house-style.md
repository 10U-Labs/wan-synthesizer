---
name: issues-have-no-house-style
description: No convention governs how an issue is shaped beyond one rule, that a part of the body is introduced by a ## heading and never by a bolded first sentence
metadata:
  type: feedback
---

# Issues have no house style

This repository has no convention for how an issue is written. Many issues share
headings such as `Problem` and `Proposed Solution`, and the NIST issues share
`Requirement`, `Today` and `Cost`, but none of those is a rule.

**Why:** b32edd99 deleted this repository's issue-structure rules and put
nothing in their place, which left sessions copying whatever pattern the
neighbouring issues happened to share. A pattern that was never decided cannot
be enforced, and reading one as a rule makes an issue worse by forcing content
into a heading it does not fit. `10ulabs.com` and `api.10ulabs.com` hold the
same rule, `deltahdl` holds it as `issues-have-no-fixed-form`, and this
repository adopted it on 2026-10-07 under issue #255.

**How to apply:** write or edit an issue however best says what it needs to say.
Do not add, rename or reorder sections to match the neighbours, and do not flag
a divergence from them as a problem. The form is free; the context is not, per
[issues-define-their-terms](issues-define-their-terms.md). One rule does hold: a
part of the body is introduced by a Markdown heading (`## Decision`), never by
bolding its first sentence (`**Decided:** ...`). Paragraphs are not
hard-wrapped, per
[no-wrapping-outside-md-files](no-wrapping-outside-md-files.md).
