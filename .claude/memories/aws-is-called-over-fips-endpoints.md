---
name: aws-is-called-over-fips-endpoints
description: "Every workflow that assumes a role sets AWS_USE_FIPS_ENDPOINT to true at its top, so boto3, the aws CLI, the OpenTofu provider and the S3 backend all end their TLS at a FIPS 140-validated endpoint; a new workflow carries it, and nothing in the tree holds that since the API migration"
metadata:
  type: project
---

# AWS is called over FIPS endpoints

Since 2026-09-13 (GitHub issue #221, NIST SP 800-171r3 03.13.11) every
workflow with an `aws-actions/configure-aws-credentials` step carries
`env: AWS_USE_FIPS_ENDPOINT: "true"` at its top, which the `aws` CLI,
boto3 in the post-deployment tiers, the AWS provider, the S3 backend
and `configure-aws-credentials`'s STS call all honour. S3, SSM, IAM,
STS and CloudFront have FIPS endpoints in `us-east-2` or globally, at
no charge. The browser's TLS to CloudFront and Google, and the ETLs'
TLS to `api.10ulabs.com`, are not selectable and stay as they are.

**Why:** the service-side TLS termination is the one part of the
path this system chooses, and the variable is cheaper than an endpoint
URL per client.

**How to apply:** a new workflow that assumes a role copies the `env`
block from `www_identity.yml`. The test that held every workflow to it
left with the API migration, so since then a workflow without it is
found by reading, not by a run. A service with no FIPS endpoint would
fail with an unresolved `<service>-fips.us-east-2.amazonaws.com` on its
first call; none in use here does.
