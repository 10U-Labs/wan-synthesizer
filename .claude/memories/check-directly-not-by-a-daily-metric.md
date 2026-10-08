---
name: check-directly-not-by-a-daily-metric
description: Confirm AWS work by querying the resources themselves and taking the answer at once, never by waiting on a metric AWS publishes once a day
metadata:
  type: feedback
---

# Check directly, not by a daily metric

When AWS work needs confirming, query the resources themselves, such as `aws iam
get-role-policy` for a grant, `aws ssm get-parameter` for a parameter, or a
`GET` on the API for what an ETL loaded, and take the answer at once. Do not
wait on a metric AWS publishes once a day, such as S3's `BucketSizeBytes`, when
a direct query can say the same thing now.

**Why:** on 2026-10-07 in `10ulabs.com` a session set a job to poll a daily S3
storage metric for up to a day before closing an issue, and the user asked why
the work hung on a daily report when the answer could be had directly and at
once. Adopted here on 2026-10-07 under issue #255.

**How to apply:** write an issue's done line as a direct check. Use a daily
metric only where no direct query can answer, and say so in the issue. A
post-deployment test is the durable form of the same check, per
[cover-every-tier-the-change-touches](cover-every-tier-the-change-touches.md).
