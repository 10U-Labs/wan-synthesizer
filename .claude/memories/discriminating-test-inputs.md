---
name: discriminating-test-inputs
description: Choose every test input so wrong code gives a different answer from right code; a literal where two quantities coincide makes a test that passes with the behaviour removed
metadata:
  type: feedback
---

# Choosing an input that discriminates

Choose every input so that incorrect code would give a different answer from
correct code.

**Why:** some values make two quantities coincide, such as an offset and a count
at zero, a carrier's PoP count and its segment count on a two-PoP fixture, or a
fallback commit sha and the one the workflow passed. A test built on one of them
passes whether the behaviour exists or not, reads in the log exactly like a real
test, and does not fail when the feature is removed. CLAUDE.md holds that a
check that cannot fail is worth nothing, and this is that rule applied to a
test's literals; `assert-pytest-test-can-fail` catches a test that cannot fail
by construction, not one whose inputs happen to agree. The rule comes from
`deltahdl` and was adopted here on 2026-10-07 under issue #255.

**How to apply:** before settling on a literal, ask what the code would return
if the behaviour under test were missing. If the answer is the same value, move
the input off the coincidence: a non-zero offset, a fixture with more rows than
the default, a sha that differs from every fallback. Write the test before the
code, per [write-the-test-first](write-the-test-first.md), so the red run shows
the input discriminates.
