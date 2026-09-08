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

The code does not say it yet: `grep -ril circuit src/ lib/ test/ scripts/` returns no file at all, while `path` spells the unit some 1,600 times. Renaming that is split across two issues — GitHub issue #148 for the published surface a caller reads, GitHub issue #150 for the identifiers inside the program — and until they land, the word in a sentence is circuit and the name on disk is written exactly as it is spelled.

## Conventions

### A circuit's route is PoPs, not cities and not a path

`SynthesisPath.path` is a `tuple[str, ...]` of site ids for carrier PoPs, and it becomes `pop_ids`. Do not call it a list of cities: a city is `SiteInfo.municipality`, an attribute a PoP carries, and the PoP is the thing. It is nevertheless true that one id there means one city, because `codec.load_merged_carriers` keeps the first carrier PoP per `(municipality, state)` and drops the rest — `test_merged_carriers_collapse_a_city_across_carriers` asserts it, and that invariant is why `_cut_cities`, `flow_cuts.Separation.lost_cities` and `ceiling._no_city_twice` are accurate when they call a site id a city and why the single point of failure the synthesizer refuses is genuinely city-level.

`path` survives only where it names a file on disk and in `graphs.reconstruct_path` and `ceiling._augmenting_path`, which are graph-algorithm walks over a predecessor map and a residual network. Everything else that held the word is named for what it holds: `fiber_segments_along` for what `path_segment_keys` returns, `miles_along` for what `path_geometry_miles` adds up.

### The PoPs between the two ends are transit PoPs

A circuit's two ends are backbone nodes; the carrier PoPs it crosses in between are transit PoPs. That is already in the code rather than a coinage — `assemble` computes `transit_ids` as the carrier PoPs on a circuit minus the backbone ids, and `collections.site_role` serves `"transit"` on every entry of the `sites` collection. So a whole route cannot be called `transit_pops`, which would name it after its middle.

### Diverse ways out are diverse circuits

`number_of_diverse_paths` is how many ways out of a site the operator asks for, and every one of those ways out is ordered and paid for, so they are diverse circuits — "circuit diversity" is what a carrier is asked for. That the name is served is a reason to sequence the change behind GitHub issue #148, not a reason to keep the word. Which single word the idea should take once every spelling says circuit is GitHub issue #128's question, since the same thing is called ways out, independent paths and diverse paths in three places.

### Nothing mechanical checks this

The vocabulary rulebook that used to carry it was deleted on 2026-08-27, so no file records the settled words and no job can refuse a banned one. Every tier runs the program and asserts what it produces, and which word an identifier uses is not something a running program produces, so no test can catch this either — it is caught by reading. Recording the words somewhere a job can open, and an `assert-*` check that reads them, is the coverage both open issues ask for. See [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md).
