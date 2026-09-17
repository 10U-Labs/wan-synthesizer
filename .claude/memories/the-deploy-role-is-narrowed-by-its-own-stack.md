---
name: the-deploy-role-is-narrowed-by-its-own-stack
description: "TenULabsWanSynthesizerRole is declared in src/www/identity and applied by the role itself, holding four inline policies and no managed one, so a missing grant is fixed forward in iam.tf; the trust names GitHub's immutable subject, the OIDC provider is read by ARN, and the Api policy is the one read of /api.10ulabs.com/api-key the ETLs need"
metadata:
  type: project
---

# The deploy role is narrowed by its own stack

`src/www/identity/` declares `TenULabsWanSynthesizerRole`, the one role
every workflow assumes through `vars.OIDC_ROLE_ARN`, and
`www_identity.yml`'s `reconciliation` applies it with that same role
(GitHub issue #246, `a7ae44f8`, 2026-09-15; the first apply was seeded
by hand, since the workflow that applies the stack has to assume the
role the stack creates). The role carries no managed policy and four
inline ones — `State` over this repository's prefix of the state
bucket, `Site` over `s3://www-10ulabs-com/wan-synthesizer/*` and the
one CloudFront distribution, `Self` over the role and the OIDC
provider, and `Api`, one `ssm:GetParameter` on
`/api.10ulabs.com/api-key` (GitHub issue #247) — with
`aws_iam_role_policies_exclusive` and
`aws_iam_role_policy_attachments_exclusive` reverting anything attached
by hand on the next reconciliation.

**Why:** a role made in the console was the one privileged account with
nothing in the tree to drift from (GitHub issue #177), and the stack
asks for what the deploys do and nothing else.

**How to apply:**

- A grant a workflow newly needs surfaces as `AccessDenied` in its run;
  it is fixed forward in `iam.tf`, and the `Self` policy is what lets
  the role reapply its own stack, so never remove a grant from it
  without the reconciliation proving the stack still applies.
- The trust names the subject GitHub actually sends, and this
  repository is set to `use_immutable_subject`, so it is
  `repo:10U-Labs@240548037/wan-synthesizer@1262350676:ref:refs/heads/main`,
  never the name-based form.
- `data "aws_iam_openid_connect_provider"` by `url` calls
  `iam:ListOpenIDConnectProviders`; by `arn` it calls
  `GetOpenIDConnectProvider` alone, which is the one the role holds.
- `cloudfront:ListDistributions` takes no resource, so it is the only
  statement on `*`.
- No `kms:Decrypt` for the key: the parameter declares no `key_id`, so
  it is under the account's `aws/ssm` key, whose policy already admits
  any principal in the account that may read the parameter. No
  `apigateway:*`: the API is served at `api.10ulabs.com`, so a loader
  calls it by name.
- `test/www/identity/pre_deployment/unit/` holds the declaration to
  the grant, and the post-deployment integration tier reads the key
  under the reconciled role and never prints it; both run in
  `www_identity.yml`. IAM can refuse a grant in the apply that writes
  it, so a new grant a stack uses at once may be a red reconciliation
  followed by a green one, never a reason to widen anything.

The state and site buckets and the distribution the role touches
belong to `10U-Labs/10ulabs.com`; the distribution id is pinned in
`iam.tf`.
