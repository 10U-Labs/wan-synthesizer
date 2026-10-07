---
name: a-written-plan-is-decided
description: An issue is labelled needs decision only when CLAUDE.md, the memories, the issue, its linked issues and the code leave a real choice open; a plan the issue already states is decided, and so is a question of order
metadata:
  type: feedback
---

# A written plan is decided

When an issue already states what is to be done, that plan is the decision: carry it out, and do not turn it back into a question. Label an issue `needs decision` only for a choice that CLAUDE.md's prime directive, the memories in this directory, the issue itself, the issues it links and the code all leave open. A question they answer is acted on, with its answer and what the answer rests on written into the issue.

**Why:** a question the rules already answer has its answer. Labelled `needs decision`, it parks the issue on a person who can only restate that answer. On 2026-10-06 a session in `10ulabs.com` labelled an issue and rewrote its title as a choice between doing what the body proposed and not doing it, and the user pointed out that the move had been the plan all along. The same thing happened here on 2026-10-07, when a session asked the user to choose a point the issue it had just filed already settled. Questions of order are the usual case: the `blocked_by` links and the autopilot's selection answer them. The rule merges `10ulabs.com`'s `a-written-plan-is-decided` with the general half of `deltahdl`'s `a-question-the-rules-answer-is-not-a-decision`, and was adopted here on 2026-10-07 under issue #255.

**How to apply:** before labelling, read the issue's title and body: if they name the outcome, the label is wrong. Test the question against the directive first, then the memories, then the code. Test its premise as well as its options: a question about how two things relate does not arise if one of them is only an artifact of the implementation, and then the issue is a defect. That the work changes live data or carries a small cost is not on its own a reason to label it; a consequence the plan carries belongs in the body as a note, not as a question. Once a person does decide, the decision rewrites the issue, per [a-decision-rewrites-the-issue](a-decision-rewrites-the-issue.md).
