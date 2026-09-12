---
name: a-memory-line-never-opens-with-an-issue-number
description: markdownlint reads a line opening with #N as a heading missing its space, so a memory is reflowed until no line starts with a hash
metadata:
  type: feedback
---

# A memory line never opens with an issue number

A line in a memory that opens with `#170` or `#190` is read by markdownlint
as an atx heading with no space after the hash, and the `documentation`
run goes red on `MD018`.

**Why:** it happened on 6c504ad3, in
`a-circuit-is-owned-one-segment-at-a-time.md`, and again on ddcb9307, in
`measure-a-change-over-the-seeded-tenants.md`, each time because a
wrapped sentence broke before "GitHub issue #N" and the number landed at
the start of the next line. Each cost a fix-forward commit.

**How to apply:** when a sentence in a memory names an issue, wrap it so
`#N` follows "issue" on the same line, or move the break. The rule that
sends the fix forward is
[a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md).
