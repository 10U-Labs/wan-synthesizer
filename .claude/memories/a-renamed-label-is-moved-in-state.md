---
name: a-renamed-label-is-moved-in-state
description: An OpenTofu resource whose label changes in code carries a moved block in the same commit, or tofu destroys the old address before it creates the new one
metadata:
  type: feedback
---

# A renamed label is moved in state

A resource whose label changes in code, say `aws_iam_role_policy.api` to
`.api_key`, carries a `moved { from = ... to = ... }` block in the same commit,
so tofu renames it in state. Without one, tofu plans the old address destroyed
and the new one created.

**Why:** in `api.10ulabs.com` on 2026-09-16 a commit relabelled a CloudFront
cache policy and origin access control with no `moved` blocks. Tofu created new
ones and then tried to delete the old two before updating the distribution off
them; CloudFront refused because they were in use, and the apply halted with the
site answering 404 until two more commits cleared it. Here the risk is sharper:
`src/www/identity` is applied by `TenULabsWanSynthesizerRole`, the role it
declares
([the-deploy-role-is-narrowed-by-its-own-stack](the-deploy-role-is-narrowed-by-its-own-stack.md)),
so a relabelled role or policy destroyed mid-apply can take away the grant the
apply is running on. Adopted here on 2026-10-07 under issue #255.

**How to apply:** every label rename gets a `moved` block in the same commit.
When the old resource is already orphaned in state and still in use by a
survivor, move it to a holding label and keep it declared for one apply, then
drop it in the next commit, fixed forward per
[a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md).
