# The code is the only explanation

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Prose beside code is never checked](#prose-beside-code-is-never-checked)
  - [The reasoning goes where it is dated and attached to a change](#the-reasoning-goes-where-it-is-dated-and-attached-to-a-change)
  - [Vendored code keeps its comments](#vendored-code-keeps-its-comments)
  - [Write a new script without a main guard](#write-a-new-script-without-a-main-guard)

## Overview

Nothing here explains the code except the code. There are no docstrings and no comments in `src/`, `lib/python/`, `scripts/`, `test/`, the `.tf` files, the files under `.github/workflows/` or `src/www/spa/app.js`, and the `assert-no-comments` job fails the run when one appears. A name, a signature and the shape of a function are the whole of what a reader gets, and when that is not enough to say what something holds or does, the thing is named or shaped wrong rather than under-explained.

## Conventions

### Prose beside code is never checked

So it stops being true and nothing says when. A test fails when the code it covers changes; a sentence above that code does not. The reader who believes it — usually a Claude session, which treats a comment as evidence — works from a program that no longer exists. The other cost is the sweep: one rename of five identifiers rewrote 327 uses, and 284 of the 352 `.py` lines its commit added were prose rather than code.

### The reasoning goes where it is dated and attached to a change

A commit message says why this commit does what it does. An issue says what is wrong and what to do about it. These notes say what holds across the repository. All three are read by somebody who knows which change they are about, and none sits next to a line of code claiming to describe it forever. Where two mechanisms answer the same question and only one is reachable, the unreachable one is deleted rather than documented, because a sentence saying which is dead stops being true the same way.

### Vendored code keeps its comments

`src/www/spa/vendor/leaflet.js` keeps them, on the same ground as the wheels that ship as `aws_lambda_layer_version.solver`: it is somebody else's code, nobody here can edit it without unpinning it, and a finding against it is answerable by nobody. `assert-no-comments` skips that directory, named in the job's `--exclude 'src/www/spa/vendor/*'`, and reads no `.md` file, where prose is the content rather than a gloss on it.

### Write a new script without a main guard

`scripts/seed.py` and `scripts/assert_dataclass_field_is_read.py` end at `main`, with no `if __name__ == "__main__":` guard: coverage.py offers no command-line flag for excluding one, so a guard body pytest never runs would fail the `--cov-fail-under=100` gates. The workflows and `test/scripts/seed/pre_deployment/integration/test_cli.py` name the entry point as `python3 -c 'import seed; seed.main()'`, which reads `sys.argv[1]` exactly as `python3 scripts/seed.py` did.
