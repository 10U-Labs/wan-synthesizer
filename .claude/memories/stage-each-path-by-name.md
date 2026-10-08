---
name: stage-each-path-by-name
description: Stage every path by name, never git add -A or git add ., keep removals on git rm because one missing pathspec makes git add stage nothing, and read git status --porcelain before committing
metadata:
  type: feedback
---

# Stage each path by name

Never use `git add -A` or `git add .`. Name every path the change touched, put a
removed path on `git rm` and an added or modified one on `git add`, never both
kinds on one command, and run `git status --porcelain` between staging and
committing.

**Why:** a commit should carry exactly what the change touched. `.gitignore`
covers the session tool's own files under `.claude/`, but scratch that nothing
ignores turns up in a working tree from time to time, and `git add -A` sweeps it
in. `git add` also stages none of its pathspecs when any one of them matches
nothing on disk: it prints `fatal: pathspec ... did not match any files`, exits
non-zero and stages nothing at all. A rename produces exactly that list, since
the old path is gone from disk, and a commit made after it carries only what was
already staged. When `git add` and `git commit` are separate calls, nothing
reads that exit status; reading the index is what makes the miss visible. The
rule merges three `deltahdl` memories and was adopted here on 2026-10-07 under
issue #255.

**How to apply:** one `git rm` for what is gone, one `git add` for what is
there, then one `git status --porcelain`, compared against the list of paths the
change was meant to touch, before `git commit`.
