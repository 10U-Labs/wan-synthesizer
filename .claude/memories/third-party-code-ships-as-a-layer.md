# Third-party code ships as a layer

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Seven jobs install highspy for themselves](#seven-jobs-install-highspy-for-themselves)
  - [The layer hangs off both Lambdas](#the-layer-hangs-off-both-lambdas)
  - [The wheels are pinned by version and by sha256](#the-wheels-are-pinned-by-version-and-by-sha256)
  - [Why unpacking one under src turns the run red](#why-unpacking-one-under-src-turns-the-run-red)

## Overview

The checks on every push exist to grade the code the people working here wrote. A package this repository merely installs was written by somebody else, is graded by somebody else, and a complaint about it is a complaint nobody who reads this run can answer. So a package the synthesizer needs while it runs is shipped to AWS as a Lambda layer, built at deploy time from wheels pinned by version and by sha256, and is never unpacked into the code this repository publishes.

## Conventions

### Seven jobs install highspy for themselves

They read or run the synthesizer rather than deploy it, and `synthesizer/linear_program.py` says `import highspy` at module scope. In `.github/workflows/api_endpoint_tenants_wan_post.yml` they are `mypy-source`, `mypy-tests`, `pylint-source`, `pylint-tests`, `pre-deployment-integration-tests`, `test-repo-libraries` and `unit-tests`, each with `highspy==1.15.1` in its `pip install` line, pinned to the same version the layer ships so the runner and the Lambda never run two different solvers. Without it the job dies on the import, before it reaches the first thing it was there to check.

### The layer hangs off both Lambdas

`aws_lambda_function.synthesizer` and `aws_lambda_function.failure_handler` both take `filename` and `source_code_hash` from `data.archive_file.synthesizer` — one deployment package, two handlers in it. Attaching the layer to only the one that imports the solver today would make them two different runtimes, and the first import moved across the file would fail in production and nowhere else. `layers = [aws_lambda_layer_version.solver.arn]` is written on both.

### The wheels are pinned by version and by sha256

The step `Fetch and unpack the solver wheels the Lambda layer is built from` fetches the `highspy` 1.15.1 and `numpy` 2.3.5 wheels by their full `files.pythonhosted.org` URLs, checks both with `sha256sum -c`, and unzips them into `src/api/endpoints/tenants/wan/post/.terraform/solver_layer/python/`. Both `validate-stack` and `reconciliation` run that step before `tofu`, because `data "archive_file" "solver_layer"` reads that directory during the plan and the plan fails outright if it is not there. The sha256 is what turns a pin into a guarantee: a file replaced on PyPI fails on the runner rather than reaching AWS. AWS caps a function and its layers at 250 MB unpacked and the two wheels come to roughly 75 MB, so the next runtime dependency goes into the same layer the same way — a URL, a sha256, an `unzip`.

### Why unpacking one under src turns the run red

`data "archive_file" "synthesizer"` in `src/api/endpoints/tenants/wan/post/main.tf` zips the whole of that stack's `lambdas/` directory, so the obvious place for a dependency — beside `lambdas/synthesizer/`, where the import would resolve without a layer at all — is inside the tree three jobs read. `pylint-source` and `mypy-source` are pointed at the synthesizer's own directory with `lambdas` on their path, so mypy follows the import into whatever is unpacked there, and `copy-paste-source` runs `jscpd --threshold 0` over it, where a package carrying two similar files of its own is a duplicate found. The findings are unanswerable in both directions, and `reconciliation` needs every gate in the workflow, so nothing deploys until the complaint about somebody else's code is cleared.
