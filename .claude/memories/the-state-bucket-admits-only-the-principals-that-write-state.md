---
name: the-state-bucket-admits-only-the-principals-that-write-state
description: "10ulabs-terraform-state-us-east-2 is declared in 10U-Labs/10ulabs.com's bootstrap stack, denies every principal its policy does not name, keeps every version of every state for 90 days, and is where a new state-writing role is admitted"
metadata:
  type: project
---

# The state bucket admits only the principals that write state

`10ulabs-terraform-state-us-east-2`, which holds every stack's state in
this repository and in `10U-Labs/10ulabs.com`, is declared in that
repository's `src/bootstrap/state.tf` (GitHub issue #213, 2026-09-13).
Its policy denies `s3:*` to every principal but the account root, the
admin IAM user, `TenULabsGitHubActionsRole` and
`TenULabsWanSynthesizerRole`, on top of the TLS-only deny, SSE-S3,
public access blocked and access logging it already had; versioning is
Enabled with noncurrent versions expiring at 90 days, reversing that
repository's 750f11a1, which had suspended it because nothing read an
old copy back, since a state history is the change record NIST SP
800-171r3 03.13.08 asks for and #212 had already taken the key out of
the state. The bootstrap stack let go of `TenULabsWanSynthesizerRole`
in the same commit through `removed` blocks, since
[the-deploy-role-is-narrowed-by-its-own-stack](the-deploy-role-is-narrowed-by-its-own-stack.md)
had made `src/api/common/identity` its declaration and a bootstrap apply
would have re-attached `AdministratorAccess`.

**Why:** a same-account bucket-policy `Allow` is additive with a role's
identity policy, so naming the wan-synthesizer role in the `Allow` would
have opened every stack's state to it; it is named only as an exception
to the `Deny`, and its own `state` inline policy stays what bounds it.

**How to apply:** a new role that must read or write state is added to
the `DenyEveryoneElse` exception list in that `state.tf` in the same
commit that creates it, or its first `init` is an `AccessDenied`. The
bootstrap tests hold the exception list to exactly those four
principals. Delete markers left by `use_lockfile` are removed only once
their noncurrent version has expired, so the stale-marker test there
looks back 97 days, not 7.
