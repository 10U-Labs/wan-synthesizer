---
name: a-decision-rewrites-the-issue
description: When a person settles an issue labelled needs decision, the decision is written into its title and body and the label comes off; it is never posted as a comment
metadata:
  type: feedback
---

# A decision rewrites the issue

When a person settles an issue labelled `needs decision`, the decision goes into
the issue itself: its title is rewritten if the decision changes what the issue
asks for, its body is rewritten to state what was decided and what the fix is,
and the `needs decision` label is removed. No comment is posted.

**Why:** the issue is read as the current statement of the work, so it has to
say what is now true. A decision left in a comment leaves the body still asking
the question it answered, and the next session reads the question. The user set
the rule in `api.10ulabs.com` when a session offered to post a decision as a
comment; `10ulabs.com` adopted it on 2026-10-06, and this repository on
2026-10-07 under issue #255.

**How to apply:** on a decision, run `gh issue edit N --title ... --body-file
... --remove-label "needs decision"` before starting the work. Any other update
to an issue is made the same way, by rewriting it, per
[issues-state-conclusions-not-the-trail](issues-state-conclusions-not-the-trail.md).
The exceptions are the finding that closes an issue whose premise is false
([an-issue-whose-premise-is-false-is-closed-with-the-finding](an-issue-whose-premise-is-false-is-closed-with-the-finding.md))
and the results of an analysis
([an-analysis-issue-asks-for-analysis-only](an-analysis-issue-asks-for-analysis-only.md)),
which go in comments.
