# The test tree splits on deployment phase, then on tier

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A tier directory appears when a test exists to put in it](#a-tier-directory-appears-when-a-test-exists-to-put-in-it)
  - [The phase is the top split](#the-phase-is-the-top-split)
  - [What a test drives decides its tier](#what-a-test-drives-decides-its-tier)

## Overview

Every subsystem under `test/` has the same four directories available to it, and the first split is whether a deployment has to exist:

```text
{subsystem}/
├── pre_deployment/
│   ├── unit/
│   └── integration/
└── post_deployment/
    ├── integration/
    └── e2e/
```

## Conventions

### A tier directory appears when a test exists to put in it

And not before. `test/scripts/seed/` has no `post_deployment/integration/`, because there is no deployed `seed` whose shape could be read. `test/api/endpoints/tenants/wan/post/` has no `e2e/`, because the files under its `post_deployment/integration/` measure the deployment rather than making a caller's journey. An absent directory is the honest answer, not a gap to fill.

### The phase is the top split

`docs/tenets/tests/OVERVIEW.md` says a tier may presume something exists, and two of the four presume a deployment: post-deployment integration asks what shape it came out, and end to end asks what a caller receives from it. Neither can be attempted on a bare checkout. The other two run anywhere.

### What a test drives decides its tier

Not how much of the program it strings together. `test/scripts/seed/pre_deployment/integration/test_cli.py` runs `python -m seed` as its own subprocess over the repository's real `data/` and `etc/`, which sounds like the whole journey, and it is pre-deployment integration because the API it talks to is a localhost stub and nothing is deployed. The name is load-bearing: a `seeding` job gated on an `e2e-tests` job that only ever ran against a stub reports a green end-to-end tier for a test that touched nothing live.
