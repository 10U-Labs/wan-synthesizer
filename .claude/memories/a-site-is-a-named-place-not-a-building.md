---
name: a-site-is-a-named-place-not-a-building
description: A site is a named place with a coordinate and nothing smaller is modelled anywhere, so no building exists in this program and the unit of failure the directive is proved over is a city
metadata:
  type: project
---

# A site is a named place, not a building

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A site is a named place and the name is the whole of it](#a-site-is-a-named-place-and-the-name-is-the-whole-of-it)
  - [The unit of failure is a city](#the-unit-of-failure-is-a-city)
  - [Why a session reaches for the wrong word](#why-a-session-reaches-for-the-wrong-word)
  - [This was caught once and not recorded](#this-was-caught-once-and-not-recorded)
  - [Nothing mechanical checks this](#nothing-mechanical-checks-this)

## Overview

The word **building** names nothing in this program. It appears nowhere in `src/`, `lib/`, `test/`, `data/`, `etc/` or `scripts/` — the one hit in the tree is the verb in `scripts/seed.py:226`, `"merge: rebuilding the merged carriers"`. Every other occurrence is prose written in a GitHub issue by a session here, nine issues in all: eight of them name a building as a thing this model holds, and one corrects them.

What the program models is a **named place with a coordinate**. A tenant site, a provider region, an off-net site and a carrier PoP are four kinds of that one thing, and nothing smaller than a named place is modelled anywhere.

## Conventions

### A site is a named place and the name is the whole of it

`data/tenants/*.csv` carries one row per site under `Name,Municipality,State,Country,Latitude,Longitude,ExemptFromDistanceConstraint`. The rows are installations, depots, proving grounds and cities — `F.E. Warren AFB`, `Aberdeen Proving Ground`, `Anniston Army Depot`, `Cheongju`, `Fort Worth`. Wright-Patterson AFB is one row, not a structure.

There is no address, street, floor, suite, room or premise field in this repository. The only `address` in the tree is a Terraform resource address in `test/lib/python/test_terraform_drift/`. So a site has no interior and no postal identity, and prose that gives it one is describing a different program.

The four kinds are named in `codec.py:8-11`: `PROVIDER_KIND` is `provider region`, `CARRIER_KIND` is `PoP`, `SITE_KIND` is `Tenant site`, `OFF_NET_KIND` is `Off-net site`. Those four words are the vocabulary. See [a-way-out-of-a-site-is-a-circuit](a-way-out-of-a-site-is-a-circuit.md) for the circuit that leaves one and [a-chosen-carrier-pop-is-a-wan-pop](a-chosen-carrier-pop-is-a-wan-pop.md) for the PoP a synthesis seats a WAN in.

### The unit of failure is a city

`codec.load_merged_carriers` at `codec.py:72` keys `by_city` on `(row["municipality"], row["state"])`, keeps the first carrier PoP it meets per city and `continue`s past every other, then names the survivor after the city with `_city(row)`. `test_merged_carriers_collapse_a_city_across_carriers` in `test/api/endpoints/tenants/wan/post/pre_deployment/unit/test_parsing.py:40` asserts it.

So one vertex of the carrier graph is one city, and the 2-vertex-connected guarantee the synthesizer publishes is a guarantee about **cities**. That is what `_cut_cities`, `flow_cuts.Separation.lost_cities` and `ceiling._no_city_twice` are already saying.

This is why the word matters beyond taste. Calling a vertex a building claims a resolution the program has thrown away: it asserts the synthesizer knows two carriers sit in two different structures in Ashburn, when the merge kept one Ashburn PoP and dropped the rest unread. A pair of circuits called vertex-disjoint because they cross different buildings is a claim about the directive that no data here can back, and CLAUDE.md holds a published figure to the directive rather than the other way round. The honest sentence is that the loss of one **city** must not split the WAN.

### Why a session reaches for the wrong word

Because the settled vocabulary names roles in a graph and the directive's content is physical. `wan_pop`, `transit_pop`, `carrier_pop`, `site` and the directive's own `access node` all say what a place does for the WAN. None of them is a noun for the physical thing whose loss takes two circuits at once, which is the thing an issue about co-seating two vertices has to name — so the prose borrows `building` from generic telecom idiom, where a conduit, a building and a city are three granularities of common failure.

The replacement is the place itself. Say **city** where the claim is about the failure the directive is proved over, and say **site** or **PoP** where the claim is about a thing's part in the WAN. Do not reach below a named place for a noun, because there is nothing down there.

### This was caught once and not recorded

GitHub issue #161 carried the correction in its body and closed on 2026-09-11:

> It said these hold "the tenant's own sites, its offices and buildings". This software tracks no buildings. `locations.json` carries one row per named place with a coordinate — an installation, a depot, a campus, a city — and nothing smaller than that is modelled anywhere in this program. Wright-Patterson AFB is one row, not a structure.

Nothing else recorded it, and this directory is what a session is given at its start, so the correction could not reach the next one. GitHub issues #184 and #185 were opened on 2026-09-11, the same day #161 closed, and both say building again. The three occurrences live at the time of writing — #166, #184 and #185 — were edited to say site and city in the commit that added this file.

### Nothing mechanical checks this

For the reason [why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md) gives: a tier runs the program and judges what comes back, and a word in issue prose is not something a running program produces. Neither is a word in an identifier, which is why the two vocabulary files beside this one end the same way. Recording the settled words somewhere a job can open is GitHub issue #158 and it is open. Until then this is held by whoever reads next, and the failure mode to expect is not a wrong identifier but a confident sentence about a building in the next issue written here.
