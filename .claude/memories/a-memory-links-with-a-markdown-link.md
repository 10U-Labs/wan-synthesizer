---
name: a-memory-links-with-a-markdown-link
description: One memory names another with a Markdown link, [name](name.md), never [name](name.md), because GitHub and markdownlint do not read the double-bracket form as a link
metadata:
  type: feedback
---

# A memory links with a Markdown link

When one memory names another, it writes a Markdown link to the file,
`[a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md)`, never
the double-bracket form `[[a-rejected-push-is-fixed-forward]]`.

**Why:** b32edd99 made every link between memories a Markdown link, because
GitHub renders the double-bracket form as plain text and markdownlint cannot
check it, so a renamed or deleted memory leaves a dead reference nobody sees.
Three memories written after that came back with the double-bracket form,
because the session tool's own instructions for memories default to it.
Issue #255 converted them on 2026-10-07 and recorded the rule.

**How to apply:** when the session's own memory instructions say to link with
`[[name]]`, write `[name](name.md)` instead. A name that has no file yet is not
linked at all; file the memory first. A memory line still never opens with an
issue number, per
[a-memory-line-never-opens-with-an-issue-number](a-memory-line-never-opens-with-an-issue-number.md).
