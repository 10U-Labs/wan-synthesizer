---
name: a-lambda-role-writes-its-own-log-group-alone
description: No stack attaches a managed policy; every function's role holds an inline Logs policy of logs:CreateLogStream and logs:PutLogEvents on the one log group its logging_config names, and no inline statement is on Resource *
metadata:
  type: project
---

# A Lambda role writes its own log group alone

Since 2026-09-13 (GitHub issue #198) no stack under `src/api` declares an
`aws_iam_role_policy_attachment`. Every function's role carries an inline
policy named `Logs` granting `logs:CreateLogStream` and
`logs:PutLogEvents` on `${aws_cloudwatch_log_group.<group>.arn}:*`, where
`<group>` is the group the function's `logging_config` names, and no
inline statement anywhere names `Resource` `*`.

**Why:** `AWSLambdaBasicExecutionRole` grants `logs:CreateLogGroup`,
`logs:CreateLogStream` and `logs:PutLogEvents` on `*`, so any function
could write to, forge in or flood another function's audit records
(NIST SP 800-171r3 03.01.05 and 03.03.08). Each function is already
given its group by `logging_config` and never creates one.

**How to apply:**

- `test/lib/python/test_terraform_config/pre_deployment/integration/test_lambda_roles.py`
  reads every stack `declared_state_keys()` lists and holds the shape,
  so it runs in every workflow's `test-repo-libraries` per
  [[shared-modules-are-tested-first]]; a new function goes red there
  until its role has the policy and its `logging_config` names the group.
- Each stack's post-deployment `test_03_wiring.py` holds the live role
  through `managed_policies_of`, `log_resources_of` and `log_group_arn`
  in `test_fixtures.aws`, comparing the grant to the ARN CloudWatch
  holds for the group.
- The deploy role's `Roles` policy already carries `iam:PutRolePolicy`,
  `iam:DeleteRolePolicy` and `iam:DetachRolePolicy` on
  `wan-synthesizer-*`, which is what the swap needs; see
  [[the-deploy-role-is-narrowed-by-its-own-stack]].
