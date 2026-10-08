---
name: commit-subject-length
description: A commit subject is as long as stating the change takes, neither padded nor cut to a width, and the body is one line per paragraph with the Closes lines below it
metadata:
  type: feedback
---

# The length of a commit subject

A commit subject is as long as it needs to be to state the change: it is neither
padded to a width nor cut to one. The body is not wrapped, so each paragraph is
one line. The `Closes #N` lines sit below the body, one per issue, per
[an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md), and the
attribution lines close the message.

**Why:** a subject cut to a conventional width states less than the change it
names, and a body hard-wrapped at a column rewraps badly wherever it is read, in
`gh`, in the web view and in a terminal of another width. The rule comes from
`deltahdl/deltahdl`, and was adopted here on 2026-10-07 under issue #261.
Commits pushed before then are not rewritten.

**How to apply:** say the whole change in the subject and stop there. Write the
body one line per paragraph, as an issue body is per
[no-wrapping-outside-md-files](no-wrapping-outside-md-files.md); the
80-character wrap of [md-paragraphs-wrap-at-80](md-paragraphs-wrap-at-80.md) is
for checked-in `.md` files only.
