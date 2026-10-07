---
name: a-way-out-is-a-circuit
description: A way out of a site or a WAN PoP is a circuit, the route it takes is the carrier PoPs it runs through, and ordering and cost are outside this repository's vocabulary
metadata:
  type: project
---

# A way out is a circuit

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A circuit's route is PoPs, not cities and not a path](#a-circuits-route-is-pops-not-cities-and-not-a-path)
  - [The PoPs between the two ends are transit PoPs](#the-pops-between-the-two-ends-are-transit-pops)
  - [Diverse ways out are diverse circuits](#diverse-ways-out-are-diverse-circuits)
  - [Ordering and cost are outside the vocabulary](#ordering-and-cost-are-outside-the-vocabulary)
  - [Nothing mechanical checks this](#nothing-mechanical-checks-this)

## Overview

The synthesizer answers one question for a tenant: which ways out of each of their sites and each of the WAN PoPs a WAN should have. One such way runs from one place to another over many fiber segments, and it is a single thing that either works or does not. The word for it is **circuit**, because that is the word the network engineers who read this repository already own and the word a carrier answers to. A tenant asking a carrier for a path will be asked what they mean.

Both sides of the wire say it: the identifiers (`SynthesisCircuit`, `HomingCircuit`, `ForcedCircuits`, `independent_circuits`, `diverse_circuit_count`, `CircuitProofInputs`) and the served surface (`/homing-circuits`, `/fiber-segments` and `/backbone-circuits`, and a circuit's `route`, the carrier PoPs it runs through). `/homing-circuits` and `/fiber-segments` are two collections because no one word is true of both. A tenant's homing circuits and a provider's are held apart all the way through, `Homings(tenant, provider)` and `HomingSites(tenant, provider)`, and each list is served under the one kind it holds. What still says path on the wire is the `forced-paths` and `prohibited-paths` inputs, which are store keys and `etc/` keys as well as routes; that is GitHub issue #162.

## Conventions

### A circuit's route is PoPs, not cities and not a path

`SynthesisCircuit.pop_ids` is a `tuple[str, ...]` of site ids for carrier PoPs. Do not call it a list of cities: a city is `SiteInfo.municipality`, an attribute a PoP carries, and the PoP is the thing. It is nevertheless true that one id there means one city, because `codec.load_merged_carriers` keeps the first carrier PoP per `(municipality, state)` and drops the rest — `test_merged_carriers_collapse_a_city_across_carriers` asserts it, and that invariant is why `_cut_cities` and `flow_cuts.Separation.lost_cities` are accurate when they call a site id a city and why the single point of failure the synthesizer refuses is genuinely city-level.

`path` survives inside the program only where it names a file on disk and in `graphs.reconstruct_path` and `ceiling._augmenting_path`, which are graph-algorithm walks over a predecessor map and a residual network. Everything else that held the word is named for what it holds: `fiber_segments_along` returns the fiber segments a circuit runs over, `miles_along` adds up the miles it runs, and `strength.site_straightness` measures `along_fiber`.

### The PoPs between the two ends are transit PoPs

A circuit's two ends are WAN PoPs; the carrier PoPs it crosses in between are transit PoPs. That is already in the code rather than a coinage — `assemble` computes `transit_ids` as the carrier PoPs on a circuit minus the WAN PoP ids, and `collections.site_role` serves `"transit"` on every entry of the `sites` collection. So a whole route cannot be called `transit_pops`, which would name it after its middle.

### Diverse ways out are diverse circuits

`number_of_diverse_circuits` is how many ways out of a WAN PoP the operator asks for — the knob sits under the `backbone:` block of every `etc/*.yml`, and a WAN PoP is not a site (GitHub issue #224) — and each of those ways out is a circuit in its own right, so they are diverse circuits — "circuit diversity" is what a carrier is asked for. That is why `independent_circuits`, `independent_circuit_ceiling`, `diverse_circuit_count`, `diverse_circuit_ceilings` and `DiverseCircuitBounds` all say circuit.

A served key and the identifier read off it cannot be renamed apart, so a rename of either moves the whole chain in one commit: the identifiers, the stored resource, the served status and report keys, the OpenAPI document and every `etc/*.yml` that names it. It is a breaking change for every caller.

Which single word the idea should take is still GitHub issue #128's question: the same thing is called ways out, independent circuits and diverse circuits in three places, and this rename settled only that none of them says path.

### Ordering and cost are outside the vocabulary

Nothing here is about ordering anything or about what anything costs. The synthesizer synthesizes a WAN from a tenant's inputs — which carrier PoPs become WAN PoPs, and which circuits join them — and that is the whole of what it models. A circuit is a connection that either works or does not, never a purchase, a line item or a charge, and no name, string or served key should say otherwise.

Fiber follows the same rule: a fiber segment is what a synthesized circuit runs over, one circuit runs over many of them, and two circuits can run over the same one. So a figure adding up fiber is the miles a WAN's circuits **run over**, never miles ordered. The published-synthesis library's figure is `fiber_miles_run_over`, and a test says the WAN runs over a carrier's fiber, never that a circuit was ordered from it. What keeps the word is sequence rather than purchase: `ceiling.py`'s local `ordered = sorted(...)` and the ordered pair a forced home resolves to.

The rule reaches prose as well as identifiers. The floor is a figure in miles, so it is **stated over** or **computed over** a set of rows, never priced over them, and a shorter circuit is shorter, never cheaper. On 2026-09-12 the operator asked why GitHub issue #172 said "priced" when nothing here has a financial cost; the word had come in from linear-programming jargon, where pricing is the term of art for evaluating an objective over rows, and it had spread to the titles of #152, #154, #156 and #175 and to commit `d963382f` before anyone read it as the claim it makes. #172 and #175 were reworded that day, and GitHub issue #189 asks `ceiling.py` to drop `_Costs`, `costs` and `_cheapest_runs`, the one module #61 and #115 left saying cost.

### Nothing mechanical checks this

The vocabulary rulebook that used to carry it was deleted on 2026-08-27. This file records the settled words again, but no job opens it, so nothing refuses a banned spelling and nothing holds the rename in place. Every tier runs the program and asserts what it produces, and which word an identifier uses is not something a running program produces, so no test can catch this either — it is caught by reading. Recording the words somewhere a job can open is GitHub issue #158, and a check that the five hand-written lists of published resource names agree is GitHub issue #159 — which #148 said should land before it and did not, so the rename above was checked by reading the five lists against each other by hand. See [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md).
