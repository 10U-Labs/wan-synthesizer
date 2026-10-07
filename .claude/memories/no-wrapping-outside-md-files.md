---
name: no-wrapping-outside-md-files
description: Text written outside the repository's .md files is never hard-wrapped; an issue body or comment has one line per paragraph and per list item
metadata:
  type: feedback
---

# No wrapping outside .md files

Do not hard-wrap text written outside the repository's `.md` files. A GitHub issue body or comment gets one line per paragraph and per list item, with no newline inside either.

**Why:** wrapping at a column exists to keep the diffs of checked-in files readable. An issue body has no diff to keep clean, GitHub wraps it to the reader's own width, and hard newlines make the web editor and quote-replies awkward. The rule comes from the `assert-*` repositories by way of `10ulabs.com`, and was adopted here on 2026-10-07 under issue #255.

**How to apply:** everywhere outside the repository's `.md` files, write each paragraph as a single line. Do not call this soft-wrapping: there is no wrapping of any kind. How an issue is otherwise shaped is [issues-have-no-house-style](issues-have-no-house-style.md).
