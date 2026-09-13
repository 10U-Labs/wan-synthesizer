---
name: the-deploy-role-is-narrowed-by-its-own-stack
description: "TenULabsWanSynthesizerRole is declared in src/api/common/identity and applied by the role itself, so a missing grant is measured by dispatching every workflow and fixed forward, the trust names GitHub's immutable subject, DescribeLogGroups is evaluated against log-group::log-stream:, the OIDC provider is read by ARN, and seed.yml assumes the one-grant TenULabsWanSynthesizerSeedRole the same stack declares"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c95dc98-0abc-45ab-b810-014b26c75379
  modified: 2026-09-13T02:23:19.285Z
---

# The deploy role is narrowed by its own stack

`src/api/common/identity/` declares `TenULabsWanSynthesizerRole`, the
one role every workflow assumes through `vars.OIDC_ROLE_ARN`, and
`api_common_identity.yml` applies it with that same role. Since
2026-09-13 (`e0cff2e`) the role carries no managed policy and seven
inline ones, each statement naming its resources, with
`aws_iam_role_policies_exclusive` and
`aws_iam_role_policy_attachments_exclusive` reverting anything attached
by hand on the next reconciliation.

**Why:** a role made in the console was the one privileged account with
nothing in the tree to drift from (GitHub issue #177). Its actions were
read from the trail's own S3 logs
(`s3://10ulabs-central-logs-us-east-2/cloudtrail/`), which cover the
role's whole life and take minutes to scan, where
`cloudtrail lookup-events` is throttled to a crawl.

**How to apply:**

- A grant the trail cannot show (S3 data events are not logged; a
  provider upgrade adds a call) surfaces only as `AccessDenied` in some
  later reconciliation. Measure it by `gh workflow run <workflow>.yml
  --ref main` for every deploying workflow after the identity stack
  applies, and fix forward in `iam.tf`; the `Self` policy is what lets
  the role reapply its own stack, so never remove a grant from it
  without the dispatch proving the stack still applies.
- The trust names the subject GitHub actually sends, and this repository
  is set to `use_immutable_subject`, so it is
  `repo:10U-Labs@240548037/wan-synthesizer@1262350676:ref:refs/heads/main`,
  never the name-based form. `GITHUB_REPOSITORY_ID` and
  `GITHUB_REPOSITORY_OWNER_ID` in the run are what the pre-deployment
  test holds it to.
- `logs:DescribeLogGroups` is evaluated against
  `arn:aws:logs:<region>:<account>:log-group::log-stream:`, not against
  the groups it lists; a prefix-scoped grant matches nothing.
- `data "aws_iam_openid_connect_provider"` by `url` calls
  `iam:ListOpenIDConnectProviders`; by `arn` it calls `GetOpenIDConnectProvider`
  alone, which is the one the role holds.
- `lambda:ListFunctions`, `cloudfront:ListDistributions` and
  `ssm:DescribeParameters` take no resource, so they are the only
  statements on `*`, and the unit tests hold that set exactly.

The state and site buckets and the CloudFront distribution the role
touches belong to `10U-Labs/10ulabs.com`; the distribution id is pinned
in `iam.tf` and a post-deployment test holds it to serving `10ulabs.com`.

## The seed assumes a role that can only read the key

Since 2026-09-13 (GitHub issue #197) the same stack declares
`TenULabsWanSynthesizerSeedRole`, trusted by the one `trust` document
and granted `ssm:GetParameter` on `/wan-synthesizer/api-key` and
nothing else. `seed.yml` assumes it through `vars.SEED_ROLE_ARN` in
the three jobs that reach the API (`seeding`, `wait-for-every-wan`,
`e2e-tests`), and its `test-repo-libraries` job assumes no role at all,
the shared modules being exercised against literals. Every other
workflow keeps `vars.OIDC_ROLE_ARN`; a unit test holds `seed.yml` to
naming the seed variable alone, and a post-deployment test holds the
live role to exactly one action.

**Why:** seeding is what the API key exists for and needs one read,
while the deploy role can replace every Lambda (NIST SP 800-171r3
03.01.06, privileged accounts for privileged functions only).

**How to apply:**

- The deploy role declares the seed role through the
  `DeclareTheSeedRole` statement of its `Roles` policy, and
  `aws_iam_role.seed` `depends_on` that policy. IAM still refused the
  `CreateRole` the same apply issued a second after the grant landed
  (run 34735362074), so a new grant a stack uses in the apply that
  writes it is a red reconciliation followed by a green one, never a
  reason to widen anything.
- A write the seed newly needs is a defect in the API's authorizer,
  never a grant to add here.
- The check that every state object in the bucket is a stack still in
  the tree reads live S3, so it is the identity stack's post-deployment
  `test_04_state_objects.py`, under the deploy role; the shared modules'
  own tests touch nothing live, which is what lets the seed's
  `test-repo-libraries` run with no role.
