# Say peers and circuits

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A city every circuit crosses is a single point of failure](#a-city-every-circuit-crosses-is-a-single-point-of-failure)
  - [Identifiers are spelled in these words too](#identifiers-are-spelled-in-these-words-too)
  - [Peers and diverse circuits are different things](#peers-and-diverse-circuits-are-different-things)
  - [Say the word for the thing](#say-the-word-for-the-thing)
  - [Sites, backbone nodes and access nodes](#sites-backbone-nodes-and-access-nodes)
  - [There is no map](#there-is-no-map)
  - [Which word for which thing](#which-word-for-which-thing)

## Overview

Two words carry almost every question about a backbone: the peers a site is joined to, and the circuits between them. A peer is another backbone node this one has a circuit to. A circuit is one way from one site to another, crossing whatever cities the fiber makes it cross, and it is also the thing an operator orders and pays for every month — so the number of circuits out of a site is at once a fact about the fiber segments and a line on the bill.

## Conventions

### A city every circuit crosses is a single point of failure

Say that, in full — not "chokepoint" and not "cut city". Lose that one city and the site is cut off, however many circuits it holds. `synthesizer.flow_cuts.weakest_separation` asks how much has to be lost before a site is cut off from its peers, `synthesizer.backbone._no_single_point_of_failure` refuses to drop a circuit whose loss would leave such a city where none stood before, and `synthesizer.validation.diverse_path_count` counts the circuits out of a site that no single city's loss takes two of.

### Identifiers are spelled in these words too

A function called `diverse_mesh_routes` beside prose about circuits is the same synonym problem one layer down, and worse there, because a reader who greps for the word they were given finds nothing. An identifier spelled with a banned word is wrong and gets renamed. Most names on disk are still spelled with path — `AccessPath`, `SynthesisPath`, `drawn_paths`, `paths_per_peer` — and until each is renamed it is written exactly as it is spelled, with circuit in the sentence around it, because a wrong name costs more than an inconsistent one. Names a caller already sees keep their word until somebody deliberately changes the API: the published `paths` and `backbone-links` collections, the `link_kind` field, the `number_of_diverse_paths` key every tenant's `etc/*.yml` sets, and the `ValidationReport` keys, whose readers are outside this repository. Old text is left alone unless the file is being changed for some other reason.

### Peers and diverse circuits are different things

Conflating them hides defects. `number_of_diverse_paths` is how many ways out of a site the operator asks for, and `synthesizer.survivable.select_fiber` selects the fiber for the whole synthesis so that every backbone node holds that many ways out no one city's loss takes two of. `synthesizer.backbone._ways_out_of` then reads a site's circuits off the fiber that was selected, so which peers a site ends up joined to falls out of that reading rather than being decided before it. How many circuits one pair is drawn with is a separate question, answered by `synthesizer.ceiling.paths_per_peer`, and the answer is one unless there are too few peers to reach.

### Say the word for the thing

Do not say **path**: it is the graph theorist's word, and a reader told a pair holds two circuits cannot tell whether the two paths in the next paragraph are the same two or two more. Do not say **route**, for the same synonym reason even though it means the right thing. Do not say **cable** or **span**: the thing both reach for is a fiber segment, one length of fiber between two adjacent points, and a circuit rides many of them. Do not say **link** at all: it was one word covering four, so a reader told a site holds four links could not tell whether four fiber segments, four circuits, four homings or four operator instructions were meant. Do not say **design**: a solver computes the answer from the PoPs, the fiber segments and a tenant's requirements, so what comes back is a synthesis and nobody sat down and drew it.

### Sites, backbone nodes and access nodes

Carrier PoPs, tenant sites, provider regions and off-net sites are all sites, and there are two kinds. A backbone node is a site the mesh seats in the backbone tier, capped by `backbone.node_count.max` in the tenant's `etc/*.yml`. An access node homes into the backbone rather than meshing: a tenant site or a provider region, joined to its backbone node by an `AccessPath`. Say which kind whenever the sentence turns on it, because almost every rule in the synthesizer applies to one kind and not the other; "site" on its own is right when the sentence is true of both. Write "node" only as "backbone node" or "access node": a bare `node` says neither which kind is meant nor that either kind is required.

### There is no map

The word means only the carriers' published network maps in `data/raw/`, which no code opens. What the synthesizer is given is the PoPs, fiber segments, tenant sites, provider regions and off-net sites that `scripts/seed.py` PUTs into S3 from the CSV files under `data/`.

### Which word for which thing

| thing | word |
| --- | --- |
| one length of fiber between two adjacent points | fiber segment, or its type `FiberSegment` — never span or cable |
| one way from one site to another | circuit — never path or route |
| what an operator orders and pays for monthly | circuit |
| two sites joined by at least one circuit | a pair |
| the site at the other end of a pair | peer |
| a city that every circuit out of a site crosses | single point of failure |
| what the synthesizer hands back | synthesis — never design |
| any carrier PoP, tenant site, provider region or off-net site | site — never a bare `node` |
| a site the mesh seats in the backbone tier | backbone node |
| a tenant site or provider region homing into the backbone | access node |
| a tenant site or provider region joined to its backbone node | access circuit — never link |
| how many backbone nodes an access node homes into | homing degree — never a link count |
| what an operator instructs be drawn or dropped | a forced circuit or a removed circuit — never link |
