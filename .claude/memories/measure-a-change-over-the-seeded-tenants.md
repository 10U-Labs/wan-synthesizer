---
name: measure-a-change-over-the-seeded-tenants
description: "Every tenant's published figures are reproducible from data/ and etc/ alone, with no deploy, which is how a commit message gets its before/after table"
metadata: 
  node_type: memory
  type: project
  originSessionId: 564c2428-3074-4656-8f9f-501045aecb3d
  modified: 2026-09-10T12:20:57.955Z
---

# Measure a change over the seeded tenants

Commit messages here carry a table of the fiber miles each tenant's WAN runs
over against the floor published beside them, before and after. Those figures
do not need a deploy: the merged carrier graph and every tenant's inputs are
reproducible from `data/` and `etc/` alone.

Stamp every `data/pops/*.csv` and `data/fiber_segments/*/*.csv` row with the
carrier its file is named for and hand the rows to `codec.load_merged_carriers`
— that is what `carriers/merge` does. `scripts/seed.py` already reads them:
`_carrier_names`, `_rows` and `_fiber_segment_rows`. Then mirror
`seed.push_tenants` for one `etc/*.yml` into the dict `config.app_config_from_parts`
expects, load the tenant's own sites with `codec.load_sites`, `load_regions` and
`load_off_net`, and run `dual_home`, `apply_role_overrides`, `synthesize_two_tier`
and `finalize`. Read `synthesis.metrics.physical_miles`,
`.backbone_lower_bound_miles`, and the validation keys
`backbone_mesh_independence_deficient` and `backbone_mesh_cut_pops`.

The seven tenants are two-pop, daf, dow, f-35, minuteman, ***REMOVED*** and ***REMOVED***;
the last two publish 4,186.183 miles and nothing at all. A run costs a few
seconds a tenant and needs `highspy` installed.

On `4faba347` this returned the tenant then called two-node 4,004.949 against a
floor of 4,004.949, daf 9,556.587 against 12,247.290, dow 10,323.419 against
11,991.811, f-35 9,730.228 against 7,241.423 and minuteman 8,265.429 against
7,003.212, each matching what `e2e-tests` read off the deployed API in run
`34440829190` to the thousandth.

f-35 has since moved to 9,851.286 against a floor of 7,017.961, which is 1.40
times the floor and fails
`test_no_published_network_runs_more_than_a_tenth_further_than_the_floor_it_publishes`.
That pair came back byte-identical from runs `34481718368`, `34538745937`,
`34540870572` and `34550736476`, on four different tips, so a `seed` run that is
red on f-35 alone and on that one assertion is the state `seed` was already in —
not something the tip under test did. It is what GitHub issues #175, #172, #171
and #170 are about. Repetition of a figure is also the only tell for the race in
[seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md), so read
which assertion failed before concluding either.

This measures a change; it does not verify one. What is green is still CI's to
say, per [ci-is-the-source-of-truth](ci-is-the-source-of-truth.md), and reading
the deployed figures after a synthesizer change has a race of its own:
[seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md).
