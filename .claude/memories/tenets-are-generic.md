# The tenets are generic, and the repository follows them

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A tenet names no tool, directory or count](#a-tenet-names-no-tool-directory-or-count)
  - [Duplication drifts with nothing to signal it](#duplication-drifts-with-nothing-to-signal-it)

## Overview

`docs/tenets/tests/` holds tenets, not documentation of the test suite. A tenet is true whatever the repository holds: it names no language, no tool, no directory, no resource and no count. The repository is what has to change to match, never the other way round.

## Conventions

### A tenet names no tool, directory or count

So a tenet says "one test file per unit of source, named for the unit it covers", not which files cover which module. It says "a copy-paste gate runs at a zero-tolerance threshold", not which tool runs it. It says "put shared setup at the highest scope where it applies", not what lives in the shared helpers today. Layout, tool names, step names, inventories of existing utilities and counts of existing tests all belong to the repository, which already states them and states them correctly.

### Duplication drifts with nothing to signal it

Anything written into a tenet that the repository also states is a copy, and it drifts with nothing to signal it. Removing from a tenet what the repository does not use is right; replacing it with a description of what the repository does use is not.
