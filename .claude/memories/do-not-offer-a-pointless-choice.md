---
name: do-not-offer-a-pointless-choice
description: Where the options differ in nothing the user cares about, pick one and say which instead of asking
metadata:
  type: feedback
---

# Do not offer a pointless choice

Where the options differ in nothing the user cares about, pick one and say which.

**Why:** asking makes the user work out that the question did not matter, which costs them more than the choice was worth. The rule comes from the `assert-*` repositories and was adopted here on 2026-10-07 under issue #255.

**How to apply:** before putting a choice to the user, ask what would differ for them under each option. If nothing would, choose, and mention the choice in a line. A choice that does matter is asked one at a time, per [one-question-at-a-time](one-question-at-a-time.md).
