# A test runs in the workflow the change it guards arrives on

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A test about a rebuilt WAN runs in seed.yml](#a-test-about-a-rebuilt-wan-runs-in-seedyml)
  - [A test about an API behaviour or its deployment runs in that endpoint workflow](#a-test-about-an-api-behaviour-or-its-deployment-runs-in-that-endpoint-workflow)
  - [A test over shared machinery runs in every workflow that imports it](#a-test-over-shared-machinery-runs-in-every-workflow-that-imports-it)
  - [The consequence that is accepted](#the-consequence-that-is-accepted)
  - [The directory and the workflow are separate questions](#the-directory-and-the-workflow-are-separate-questions)

## Overview

A test is worth nothing in a workflow the change it guards does not trigger. So the question "which workflow runs this test" is answered by asking what kind of push would break it, and putting the test where that push goes — not by which subsystem the test file happens to sit under.

## Conventions

### A test about a rebuilt WAN runs in seed.yml

`test/scripts/seed/post_deployment/e2e/test_delivered_syntheses.py` measures each tenant's published network against the `backbone` block of its `etc/*.yml`. What breaks it is an edit to `etc/`, and a push touching `etc/` alone starts `seed.yml` and nothing else. `seed.yml` is also the workflow that delivers the edit: its `seeding` job runs `scripts/seed.py`, which PUTs the inputs and then POSTs one build per tenant. Deliver, rebuild and measure are three steps of one thing, and they run in one workflow in that order.

### A test about an API behaviour or its deployment runs in that endpoint workflow

`test_01_existence.py`, `test_02_configuration.py` and `test_03_wiring.py` under `test/api/endpoints/tenants/wan/post/post_deployment/integration/` ask whether the synthesizer Lambda exists, whether its runtime and memory match the declaration, and whether its role can reach the store. Each breaks when `src/api/endpoints/tenants/wan/post/**` changes, which is what `api_endpoint_tenants_wan_post.yml` triggers on, and each runs there after `reconciliation` applies the stack.

### A test over shared machinery runs in every workflow that imports it

The nine modules in `lib/python/` have no workflow of their own and no single consumer, so the rule above picks out no one workflow. The import that decides it is the transitive one: `test_handler_contracts` imports `test_module_utils` and `test_s3_store_mock`, and `test_fixtures.aws` and `test_terraform_drift` import `test_terraform_config`, which imports `repo_utils` — so a defect in `test_module_utils` breaks workflows whose test files never name it.

### The consequence that is accepted

A synthesizer change deploys in `api_endpoint_tenants_wan_post.yml` but is not measured against a rebuild until the next push that touches something `seed.yml` triggers on. Moving `reconciliation` into `seed.yml` was offered as the alternative and declined.

### The directory and the workflow are separate questions

Which directory the file sits in is answered by what the test checks rather than by what runs it, and the two agreeing is the ordinary case. Where they land apart — `test/lib/python/test_published_syntheses/**` sits with the module it covers and is run by workflows that do not own it — the workflow must list that file and its whole conftest chain in its `paths`, or a change to the test does not run the test. One entry, `test/lib/python/**`, is what that costs, because it covers the conftests too.
