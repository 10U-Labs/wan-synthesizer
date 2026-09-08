---
name: cover-every-tier-the-change-touches
description: Unit tests alone are not sufficient: add coverage at every tier the change touches, one assert per pytest
metadata:
  type: feedback
---

# Cover every tier the change touches

Unit tests alone are not sufficient: add coverage at every tier the change touches, one assert per pytest.

Which tiers exist and where they sit is [[the-test-tree-splits-on-deployment-phase]]; which workflow runs the new test is [[where-a-test-runs-follows-what-starts-it]]; the tests are written before the code, per [[write-the-test-first]].
