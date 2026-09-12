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
the last two publish 4,186.183 miles and nothing at all. A run costs up to a
minute a tenant and needs `highspy`, which no Python on the machine has: make a
venv in the session scratchpad, never under the repository, and `pip install
highspy pyyaml` into it. Measuring is not the local verification
[ci-is-the-source-of-truth](ci-is-the-source-of-truth.md) forbids — it is how
a claim about the synthesizer is checked before a test is written for it.

On `4faba347` this returned the tenant then called two-node 4,004.949 against a
floor of 4,004.949, daf 9,556.587 against 12,247.290, dow 10,323.419 against
11,991.811, f-35 9,730.228 against 7,241.423 and minuteman 8,265.429 against
7,003.212, each matching what `e2e-tests` read off the deployed API in run
`34440829190` to the thousandth.

Since 6c504ad3 let a circuit change hands between carriers, the seven published
two-pop 3,884.265 against 3,884.265, daf 8,212.251 against 7,043.473, dow
7,581.802 against 7,361.252, f-35 7,575.128 against 6,150.391, minuteman
4,712.437 against 4,712.437, ***REMOVED*** 4,186.183 against 4,186.183 and ***REMOVED***
nothing, matching run `34670636252` re-run against the deployed Lambda to the
thousandth. daf at 1.166 and f-35 at 1.232 failed
`test_no_published_network_runs_more_than_a_tenth_further_than_the_floor_it_publishes`,
which was the one red assertion in `e2e-tests` for the run of commits up to
d400877f, and was GitHub issue #175's. dfd1ccdb closed #173 and #175 by
crediting a peer every circuit that shares no PoP between and selecting the
fiber over the rows the floor is stated over, and since then every tenant with
a mesh runs exactly its floor: two-pop 3,884.265, daf 7,043.473, dow
7,361.252, f-35 5,735.325 (which selects Richmond, VA where it selected New
Orleans, LA), minuteman 4,712.437, ***REMOVED*** 4,186.183 and ***REMOVED*** nothing. Run
`34696243921`, started by hand after 6918bbd6 deployed, read them off the
deployed API to the thousandth and is green on every tier; the seed run a
synthesizer push starts itself grades the WANs the previous Lambda built, per
[seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md).
Holding a tenant asking for one circuit to the directive, for GitHub issue
#190, moved ***REMOVED*** alone: it publishes 8,407.716 against 8,407.716 over two
transatlantic circuits sharing no PoP, where it published 4,186.183 over one.
A selection or a floor that reads differently from those figures is the tip
under test's doing.
Repetition of a figure is also the only tell for the race in
[seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md), so
read which assertion failed before concluding either.

This measures a change; it does not verify one. What is green is still CI's to
say, per [ci-is-the-source-of-truth](ci-is-the-source-of-truth.md), and reading
the deployed figures after a synthesizer change has a race of its own:
[seeding-races-the-routing-deploy](seeding-races-the-routing-deploy.md).
