---
name: the-test-tree-splits-on-deployment-phase
description: Every subsystem under test/ is laid out as pre_deployment/{unit,integration} and post_deployment/{integration,e2e}
metadata:
  type: project
---

# The test tree splits on deployment phase

Every subsystem under `test/` is laid out as `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}`, and a tier directory appears only when a test exists to put in it. The deployment phase is the top split because neither post-deployment tier can be attempted until there is a deployment to call.

A journey against a localhost stub is pre-deployment integration however end-to-end it looks: `test/scripts/seed/pre_deployment/integration/test_cli.py` drives `scripts/seed.py` as a subprocess and touches nothing live, while `test/scripts/seed/post_deployment/e2e/test_delivered_syntheses.py` reads the deployed API.

Which directory a file sits in is a separate question from which workflow runs it: [where-a-test-runs-follows-what-starts-it](where-a-test-runs-follows-what-starts-it.md).
