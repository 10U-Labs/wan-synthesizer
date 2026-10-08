---
name: write-the-test-first
description: TDD: the test is written before the code that makes it pass, and red and green are observed in CI
metadata:
  type: feedback
---

# Write the test first

We do TDD: the test is written first, then the code that makes it pass.
Test-first means authoring order — the red and green observations belong to CI,
since nothing runs locally, per
[ci-is-the-source-of-truth](ci-is-the-source-of-truth.md).

A test that reads a file the change has not written yet does the read in a
fixture, never at module level, and never softens the missing file with a
default, a `None` or a `pytest.skip`. At module level the missing file raises
during import, which pytest reports as a collection error for the whole module;
behind a fixture only the test that asked errors, naming the missing path, which
is the red run TDD asks for. A default or a skip turns the test green before the
code exists. The red run has to fail for the reason the test names, so its
inputs are chosen per
[discriminating-test-inputs](discriminating-test-inputs.md), and a call expected
to raise is made per
[a-raise-expected-in-a-test-is-raised-in-a-fixture](a-raise-expected-in-a-test-is-raised-in-a-fixture.md).

How much to write is
[cover-every-tier-the-change-touches](cover-every-tier-the-change-touches.md).
