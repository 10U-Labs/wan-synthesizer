---
name: a-raise-expected-in-a-test-is-raised-in-a-fixture
description: assert-one-assert-per-pytest counts pytest.raises as an assert, so a call expected to raise is made in a fixture and the test asserts on the outcome alone
metadata:
  type: feedback
---

# A raise expected in a test is raised in a fixture

`assert-one-assert-per-pytest` counts a `with pytest.raises(...)` block as an assert, so a test that expects a call to raise and then asserts on a side effect holds two and is refused.

**Why:** the check runs in every workflow here, per [every-workflow-runs-the-assert-tools](every-workflow-runs-the-assert-tools.md). In `api.10ulabs.com` on 2026-09-17 a test wrapped a call in `pytest.raises(ClientError)` and then asserted that nothing was invalidated; the gate counted two asserts and the workflow went red on that test alone. The fix moved the raising call into a fixture. Adopted here on 2026-10-07 under issue #255.

**How to apply:** put the call expected to raise, with its `pytest.raises`, in a fixture the test requests, through `usefixtures` when the test needs no value from it, and assert on the outcome in the test. A test whose only claim is that the call raises keeps its `pytest.raises` as its one assert. See [cover-every-tier-the-change-touches](cover-every-tier-the-change-touches.md).
