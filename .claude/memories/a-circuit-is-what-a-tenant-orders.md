---
name: a-circuit-is-what-a-tenant-orders
description: The unit a tenant orders and pays for is a circuit, and the route it takes is the carrier PoPs it runs through
metadata:
  type: project
---

# A circuit is what a tenant orders

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A circuit's route is PoPs, not cities and not a path](#a-circuits-route-is-pops-not-cities-and-not-a-path)
  - [The PoPs between the two ends are transit PoPs](#the-pops-between-the-two-ends-are-transit-pops)
  - [Diverse ways out are diverse circuits](#diverse-ways-out-are-diverse-circuits)
  - [Nothing mechanical checks this](#nothing-mechanical-checks-this)

## Overview

The synthesizer answers one question for a tenant: which ways out of each of their sites should be ordered from a carrier. One such way runs from one site to another over many fiber segments and it is a single line on an invoice — one order, one monthly charge, one thing that either works or does not. The word for it is **circuit**, because that is the word the network engineers who read this repository already own and the word a carrier can take an order in. A tenant asking a carrier for a path will be asked what they mean.

The identifiers inside the program say it. GitHub issue #150 renamed them on 2026-09-07 — `SynthesisCircuit`, `AccessCircuit`, `ForcedCircuits`, `independent_circuits`, `diverse_circuit_count`, `CircuitProofInputs` and the rest, some 1,600 uses across `src/`, `lib/python/` and `test/`. What still spells the unit `path` is the surface a caller reads: the `paths` collection, the `access_paths`, `drawn_paths` and `summary.access_path_count` keys of the served payload, the `"path"` field on each `backbone-links` entry, the `forced-paths`, `prohibited-paths` and `backbone-number-of-diverse-paths` resources, and the `backbone_diverse_paths_*` keys of the validation report. Moving those is GitHub issue #148, which is open. So a name inside the program is a circuit; a key a caller reads is written exactly as it is served, and a name read straight off one of those resources — `Tuning.backbone_number_of_diverse_paths` — moves when the resource does and not before.

## Conventions

### A circuit's route is PoPs, not cities and not a path

`SynthesisCircuit.pop_ids` is a `tuple[str, ...]` of site ids for carrier PoPs. Do not call it a list of cities: a city is `SiteInfo.municipality`, an attribute a PoP carries, and the PoP is the thing. It is nevertheless true that one id there means one city, because `codec.load_merged_carriers` keeps the first carrier PoP per `(municipality, state)` and drops the rest — `test_merged_carriers_collapse_a_city_across_carriers` asserts it, and that invariant is why `_cut_cities`, `flow_cuts.Separation.lost_cities` and `ceiling._no_city_twice` are accurate when they call a site id a city and why the single point of failure the synthesizer refuses is genuinely city-level.

`path` survives inside the program only where it names a file on disk and in `graphs.reconstruct_path` and `ceiling._augmenting_path`, which are graph-algorithm walks over a predecessor map and a residual network. Everything else that held the word is named for what it holds: `fiber_segments_along` returns the fiber segments a circuit runs over, `miles_along` and `ceiling._miles_along` add up the miles it runs, and `strength.site_straightness` measures `along_fiber`.

### The PoPs between the two ends are transit PoPs

A circuit's two ends are backbone nodes; the carrier PoPs it crosses in between are transit PoPs. That is already in the code rather than a coinage — `assemble` computes `transit_ids` as the carrier PoPs on a circuit minus the backbone ids, and `collections.site_role` serves `"transit"` on every entry of the `sites` collection. So a whole route cannot be called `transit_pops`, which would name it after its middle.

### Diverse ways out are diverse circuits

`number_of_diverse_paths` is how many ways out of a site the operator asks for, and every one of those ways out is ordered and paid for, so they are diverse circuits — "circuit diversity" is what a carrier is asked for. That is why `independent_circuits`, `independent_circuit_ceiling`, `diverse_circuit_count`, `diverse_circuit_ceilings` and `DiverseCircuitBounds` all say circuit. `number_of_diverse_paths` itself still says path in `Tuning`, `MeshRequirements` and `BackboneConstraints` because it is the `backbone-number-of-diverse-paths` resource read down a chain, and that the name is served is a reason to sequence its change behind GitHub issue #148, not a reason to keep the word. Which single word the idea should take once every spelling says circuit is GitHub issue #128's question, since the same thing is called ways out, independent paths and diverse paths in three places.

### Nothing mechanical checks this

The vocabulary rulebook that used to carry it was deleted on 2026-08-27. This file records the settled words again, but no job opens it, so nothing refuses a banned spelling and nothing holds the rename in place. Every tier runs the program and asserts what it produces, and which word an identifier uses is not something a running program produces, so no test can catch this either — it is caught by reading. Recording the words somewhere a job can open, and an `assert-*` check that reads them, is the coverage both open issues ask for. See [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md).
