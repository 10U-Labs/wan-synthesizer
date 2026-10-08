---
name: md-paragraphs-wrap-at-80
description: In a tracked .md file prose paragraphs wrap at 80 characters; list items, headings, tables, link lines and code blocks may run long, MD013 stays disabled, and nothing checks the width
metadata:
  type: feedback
---

# Markdown paragraphs wrap at 80

In a `.md` file this repository tracks, a prose paragraph wraps at 80
characters. A list item, heading, table row, link line or code block may run
past 80 and stays on one line. A Markdown link or code span longer than 80 on
its own, such as a link to a memory with a long name, takes a line of its own
rather than being broken.

**Why:** a wrapped paragraph gives a checked-in file a readable diff, which is
the whole reason [no-wrapping-outside-md-files](no-wrapping-outside-md-files.md)
gives for wrapping anything. Folding a list item, heading or table row hurts
its reading more than the width saves. The rule comes from
`assert-one-assert-per-pytest` and `assert-pytest-class-holds-state`, and was
adopted here on 2026-10-07 under issue #260, when every tracked `.md` file but
`LICENSE.md` was rewrapped.

**How to apply:** wrap a paragraph you write or change at 80, and never let a
wrapped line open with something Markdown reads as a block marker: a `#`, per
[a-memory-line-never-opens-with-an-issue-number](a-memory-line-never-opens-with-an-issue-number.md),
a `>`, a lone `-`, `+` or `*`, or a number followed by a full stop.
markdownlint's MD013 cannot tell a paragraph from a list item, so
`documentation.yml` keeps it disabled with `--disable MD013` rather than
satisfying it by rewrapping everything. Nothing checks the width yet, so it
holds only as long as each change keeps it, and issue #269 asks for the
`assert-*` repository that would.
