# An issue states one solution

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Ask at the fork, then write down the branch that came back](#ask-at-the-fork-then-write-down-the-branch-that-came-back)
  - [Issues already on disk that carry an either](#issues-already-on-disk-that-carry-an-either)
  - [Naming the alternative that lost](#naming-the-alternative-that-lost)

## Overview

An issue is the instruction to whoever picks it up, and it has to be workable on its own. Its `Proposed Solution` names one change: this function, this file, this algorithm, this test. Not two options to weigh, not a menu with a recommendation, and never a question the reader is left holding. If the section ends with something still to decide, the issue is not finished and should not be filed.

## Conventions

### Ask at the fork, then write down the branch that came back

The trade-off behind an "either" is usually real, and the place to settle it is before the issue exists, in the conversation where the measurements are fresh and the person who can decide is present. An issue is read weeks later by somebody who cannot reconstruct that conversation, so filing the question instead of the answer moves the hardest part of the work onto them. Asking costs one turn; filing an undecided issue costs the decision being made twice, or made by whoever is in a hurry.

### Issues already on disk that carry an either

Do not pick, however clearly the text leans toward one and even when it calls one the smaller change; ask which one before editing a file, and before there is a draft, because a draft turns the question into a request to approve what is already done.

### Naming the alternative that lost

Definitive does not mean silent about what was rejected. Naming the alternative and why it lost stops the same ground being covered again.
