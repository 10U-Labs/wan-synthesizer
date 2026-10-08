---
name: an-issue-is-split-by-problem-not-by-fix
description: Issues divide the work, one indivisible problem each, and batches bring them together; an issue is never merged with another to cut the count or because they share a fix
metadata:
  type: feedback
---

# Issues divide, batches merge

The work is divided by issues, each documenting one indivisible problem, and
brought together by batches, which take every open issue of one stack into one
push. So an issue is split as finely as its problems run, and never merged with
another because they share a fix, a module or a batch: the batch already brings
them together.

**Why:** in `api.10ulabs.com` a session folded five issues into broader ones to
keep the count down, and the user corrected it: an issue is one problem, and
putting issues together is what a batch does. `10ulabs.com` adopted the rule on
2026-10-06, and this repository on 2026-10-07 under issue #255.

**How to apply:** never weigh the number of issues, and never argue that issues
belong together because they land in one batch. When unsure whether a part is
its own problem, file it apart. An issue that holds more than one problem is
split, keeping its number for one of the parts. The batching is
[a-push-solves-every-open-issue-of-one-stack](a-push-solves-every-open-issue-of-one-stack.md).
