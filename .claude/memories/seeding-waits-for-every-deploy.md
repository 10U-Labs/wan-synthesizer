---
name: seeding-waits-for-every-deploy
description: seeding runs after every workflow on the same commit that deploys something it talks to, through a wait-for-every-deploy job copied from 10ulabs.com's wait-for-api-common-routing, so a seed never grades WANs the previous Lambda built
metadata:
  type: project
---

# Seeding waits for every deploy

GitHub Actions orders nothing between workflows started by one push, so
`seeding` used to race the eight `reconciliation` jobs that ship what it
talks to: a renamed input could 403 or 404 on the old route or handler,
and a synthesizer change was seeded and graded against the Lambda the
previous commit deployed, which had to be answered with
`gh workflow run seed.yml --ref main` by hand once the deploy landed.

`wait-for-every-deploy` in `seed.yml` is the job that ends that. On a
push it polls `gh api repos/.../actions/workflows/<file>/runs?head_sha=`
for each workflow in its `WORKFLOWS` list until every run on this commit
has completed, and outputs `apply=true` only when each one ended
`success` or was never started; `seeding` reads that output in its `if`
beside the sixteen `== 'success'` gates. A `workflow_dispatch` run
started nothing beside it and waits for nothing. The shape is
`10ulabs.com`'s `.github/actions/wait-for-api-common-routing`, which
`reconciliation` reads there for the one workflow that writes the routing
it depends on; here the list is every workflow with a `reconciliation`
job, and `test_seeding_waits_for_every_workflow_that_deploys_on_the_same_commit`
fails when a workflow gains one and the list does not.

What is left of the race is only the 60 minutes the poll allows a
deploy, after which the job fails and says which workflow has not
finished. What every push runs before `seeding` is
[seed-tests-every-push](seed-tests-every-push.md); the prune's own race
was removed separately, per
[seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md).
