---
name: a-way-out-of-a-site-is-a-circuit
description: A way out of a site is a circuit, the route it takes is the carrier PoPs it runs through, and ordering and cost are outside this repository's vocabulary
metadata:
  type: project
---

# A way out of a site is a circuit

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A circuit's route is PoPs, not cities and not a path](#a-circuits-route-is-pops-not-cities-and-not-a-path)
  - [The PoPs between the two ends are transit PoPs](#the-pops-between-the-two-ends-are-transit-pops)
  - [Diverse ways out are diverse circuits](#diverse-ways-out-are-diverse-circuits)
  - [Ordering and cost are outside the vocabulary](#ordering-and-cost-are-outside-the-vocabulary)
  - [Nothing mechanical checks this](#nothing-mechanical-checks-this)

## Overview

The synthesizer answers one question for a tenant: which ways out of each of their sites a WAN should have. One such way runs from one site to another over many fiber segments, and it is a single thing that either works or does not. The word for it is **circuit**, because that is the word the network engineers who read this repository already own and the word a carrier answers to. A tenant asking a carrier for a path will be asked what they mean.

Both sides of the wire say it. GitHub issue #150 renamed the identifiers on 2026-09-07 — `SynthesisCircuit`, `HomingCircuit`, `ForcedCircuits`, `independent_circuits`, `diverse_circuit_count`, `CircuitProofInputs` and the rest, some 1,600 uses across `src/`, `lib/python/` and `test/`. GitHub issue #148 moved the served surface on 2026-09-10: the one `paths` collection became `/homing-circuits` and `/fiber-segments` because it held both and no one word is true of both, `/backbone-links` became `/backbone-circuits`, the payload keys are `homing_circuits`, `drawn_circuits` and `summary.homing_circuit_count`, and the `path` field on a circuit — the carrier PoPs it runs through — is now `route`. The `link_kind` that told the two kinds apart is gone with the bag: a fiber row needs no discriminator in a fiber collection, and a homing row carries `homing_kind` for the tenant-or-provider question GitHub issue #149 asks. What still says path on the wire is the `forced-paths` and `prohibited-paths` inputs, which are store keys and `etc/` keys as well as routes; that is GitHub issue #162 and it is open.

## Conventions

### A circuit's route is PoPs, not cities and not a path

`SynthesisCircuit.pop_ids` is a `tuple[str, ...]` of site ids for carrier PoPs. Do not call it a list of cities: a city is `SiteInfo.municipality`, an attribute a PoP carries, and the PoP is the thing. It is nevertheless true that one id there means one city, because `codec.load_merged_carriers` keeps the first carrier PoP per `(municipality, state)` and drops the rest — `test_merged_carriers_collapse_a_city_across_carriers` asserts it, and that invariant is why `_cut_cities`, `flow_cuts.Separation.lost_cities` and `ceiling._no_city_twice` are accurate when they call a site id a city and why the single point of failure the synthesizer refuses is genuinely city-level.

`path` survives inside the program only where it names a file on disk and in `graphs.reconstruct_path` and `ceiling._augmenting_path`, which are graph-algorithm walks over a predecessor map and a residual network. Everything else that held the word is named for what it holds: `fiber_segments_along` returns the fiber segments a circuit runs over, `miles_along` and `ceiling._miles_along` add up the miles it runs, and `strength.site_straightness` measures `along_fiber`.

### The PoPs between the two ends are transit PoPs

A circuit's two ends are WAN PoPs; the carrier PoPs it crosses in between are transit PoPs. That is already in the code rather than a coinage — `assemble` computes `transit_ids` as the carrier PoPs on a circuit minus the WAN PoP ids, and `collections.site_role` serves `"transit"` on every entry of the `sites` collection. So a whole route cannot be called `transit_pops`, which would name it after its middle.

### Diverse ways out are diverse circuits

`number_of_diverse_circuits` is how many ways out of a site the operator asks for, and each of those ways out is a circuit in its own right, so they are diverse circuits — "circuit diversity" is what a carrier is asked for. That is why `independent_circuits`, `independent_circuit_ceiling`, `diverse_circuit_count`, `diverse_circuit_ceilings` and `DiverseCircuitBounds` all say circuit.

This one moved as a whole chain on 2026-09-07 rather than waiting behind GitHub issue #148, because the operator asked for it directly and the word was wrong on both sides of the wire. All 132 uses went at once: `Tuning.backbone_number_of_diverse_circuits`, `MeshRequirements.number_of_diverse_circuits` and `WanPopConstraints.number_of_diverse_circuits` inside the program; the `backbone-number-of-diverse-circuits` resource and its `.json` object in the store; the `diverse_circuits` block of the served status and its `number_of_diverse_circuits` key; the `backbone_diverse_circuits_*` keys of the validation report; `src/www/api/openapi.json`; and the `number_of_diverse_circuits` key of all seven `etc/*.yml` tenant configs. It is a breaking change for every caller, which is why the whole chain had to go in one commit — a served key and the identifier read off it cannot be renamed apart.

Which single word the idea should take is still GitHub issue #128's question: the same thing is called ways out, independent circuits and diverse circuits in three places, and this rename settled only that none of them says path.

### Ordering and cost are outside the vocabulary

Nothing here is about ordering anything or about what anything costs. The synthesizer synthesizes a WAN from a tenant's inputs — which carrier PoPs become WAN PoPs, and which circuits join them — and that is the whole of what it models. A circuit is a connection that either works or does not, never a purchase, a line item or a charge, and no name, string or served key should say otherwise.

Fiber follows the same rule: a fiber segment is what a synthesized circuit runs over, one circuit runs over many of them, and two circuits can run over the same one. So a figure adding up fiber is the miles a WAN's circuits **run over**, never miles ordered. GitHub issue #153 settled the names on 2026-09-11: the published-synthesis library's `ordered_fiber_miles` is `fiber_miles_run_over`, its two test names say the WAN runs over the fiber rather than ordering it, and the three test names that had a drawn circuit ordered from a carrier now say it runs over that carrier's fiber. What keeps the word is sequence rather than purchase: `ceiling.py`'s local `ordered = sorted(...)` and the ordered pair a forced home resolves to.

### Nothing mechanical checks this

The vocabulary rulebook that used to carry it was deleted on 2026-08-27. This file records the settled words again, but no job opens it, so nothing refuses a banned spelling and nothing holds the rename in place. Every tier runs the program and asserts what it produces, and which word an identifier uses is not something a running program produces, so no test can catch this either — it is caught by reading. Recording the words somewhere a job can open is GitHub issue #158, and a check that the five hand-written lists of published resource names agree is GitHub issue #159 — which #148 said should land before it and did not, so the rename above was checked by reading the five lists against each other by hand. See [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md).
