---
name: aws-is-called-over-fips-endpoints
description: "Every Lambda's environment and every workflow that assumes a role set AWS_USE_FIPS_ENDPOINT to true, so boto3, the aws CLI, the OpenTofu provider and the S3 backend all end their TLS at a FIPS 140-validated endpoint; a new function or workflow carries it or test_fips_endpoints.py is red everywhere"
metadata:
  type: project
---

# AWS is called over FIPS endpoints

Since 2026-09-13 (GitHub issue #221, NIST SP 800-171r3 03.13.11) every
`aws_lambda_function` carries `AWS_USE_FIPS_ENDPOINT = "true"` in its
environment and every workflow with an `aws-actions/configure-aws-credentials`
step carries `env: AWS_USE_FIPS_ENDPOINT: "true"` at its top, which
boto3 in the handlers, the `aws` CLI in `seed.yml` and `www_spa.yml`,
the AWS provider, the S3 backend and `configure-aws-credentials`'s STS
call all honour. S3, SSM, Lambda, IAM, Logs, STS, API Gateway and
CloudFront have FIPS endpoints in `us-east-2` or globally, at no
charge. The browser's TLS to CloudFront and Google, and the
authorizer's call to `oauth2.googleapis.com`, are not selectable and
stay as they are.

**Why:** the service-side TLS termination is the one part of the
path this system chooses, and the variable is cheaper than an endpoint
URL per client.

**How to apply:** `test_fips_endpoints.py` in `test_terraform_config`'s
integration tier, which every `test-repo-libraries` runs, holds every
function's environment and every role-assuming workflow's `env` to it,
so a new function or workflow carries it or that job is red in every
workflow. A service with no FIPS endpoint would fail with an unresolved
`<service>-fips.us-east-2.amazonaws.com` on its first call; none in use
here does.
