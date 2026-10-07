---
name: one-question-at-a-time
description: Put one plain question to the user per message, with a recommendation, and queue the rest; when the user is lost, start again from the smallest concrete example in plain words
metadata:
  type: feedback
---

# One question at a time

Put exactly one question to the user per message. When several decisions are pending, queue each one and ask them one after another, each after the last is answered. Ask only what the issues and the rules leave open, per [a-written-plan-is-decided](a-written-plan-is-decided.md), and only where the options differ in something the user cares about, per [do-not-offer-a-pointless-choice](do-not-offer-a-pointless-choice.md).

**Why:** the user said so in `10ulabs.com` on 2026-10-06, after a session asked several questions in one message, each with background, options and recommendations. A person cannot take in and answer many questions at once the way a model can, and gets confused when handed a pile of them. Adopted here on 2026-10-07 under issue #255.

**How to apply:** lead with the question in a sentence or two of plain words, give a recommendation, and stop. Do not attach a second question, a side conflict or a list of findings to the same message. When the user says they are lost, start over from the smallest concrete example and drop this repository's own vocabulary, saying what happens and what goes wrong in words a stranger would follow, rather than restating the long version with more detail.
