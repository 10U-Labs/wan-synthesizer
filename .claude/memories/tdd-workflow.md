# Test-driven development

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Cover every tier the change touches](#cover-every-tier-the-change-touches)
  - [Test-first means authoring order](#test-first-means-authoring-order)

## Overview

We do TDD in this repository. Write the test first, then the production code that makes it pass.

## Conventions

### Cover every tier the change touches

Coverage is not one test file. Add the test at each tier the change touches, which means reading the tenets before writing anything; see [read-test-tenets-first](read-test-tenets-first.md).

### Test-first means authoring order

Not a local red-green loop. The failing observation and the passing one both belong to CI, because nothing is run locally. Put the tests and the implementation in the same commit, since a commit goes straight to `main` with no pull-request buffer to hold a red state.
