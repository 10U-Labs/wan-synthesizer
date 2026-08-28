# Say peers and circuits

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A city every circuit crosses is a single point of failure](#a-city-every-circuit-crosses-is-a-single-point-of-failure)
  - [Identifiers are spelled in these words too](#identifiers-are-spelled-in-these-words-too)
    - [An identifier spelled with a banned word gets renamed](#an-identifier-spelled-with-a-banned-word-gets-renamed)
    - [Names a caller already sees keep their word](#names-a-caller-already-sees-keep-their-word)
    - [Old text is left alone](#old-text-is-left-alone)
  - [Peers and diverse circuits are different things](#peers-and-diverse-circuits-are-different-things)
  - [Say the word for the thing](#say-the-word-for-the-thing)
    - [Do not say cable or span](#do-not-say-cable-or-span)
    - [Do not say design](#do-not-say-design)
    - [Do not say link](#do-not-say-link)
    - [Do not say path](#do-not-say-path)
    - [Do not say route](#do-not-say-route)
  - [Sites, backbone nodes and access nodes](#sites-backbone-nodes-and-access-nodes)
  - [There is no map](#there-is-no-map)
  - [Which word for which thing](#which-word-for-which-thing)
- [Notes](#notes)

## Overview

Two words carry almost every question about a backbone: the peers a site is joined to, and the circuits between them. A peer is another backbone node this one has a circuit to. A circuit is one way from one site to another, and it crosses whatever cities the fiber makes it cross — `Ashburn, VA -> Martinsburg, WV -> Pittsburgh, PA -> ... -> Minot, ND` is one circuit over nine cities. A circuit is also the thing an operator orders and pays for every month, so the number of circuits out of a site is at once a fact about the fiber segments and a line on the bill. Answer in those two words, in chat as much as in issues, and the reader can follow without opening anything.

## Conventions

### A city every circuit crosses is a single point of failure

A city that every circuit out of a site crosses is a single point of failure. Say that, in full — not "chokepoint" and not "cut city". It is the plainest statement of what is wrong and it needs no graph theory to read: lose that one city and the site is cut off, however many circuits it holds. `synthesizer.flow_cuts.weakest_separation` is what asks how much has to be lost before a site is cut off from its peers, and hands back the cities and fiber segments that come apart when the fiber selected so far falls short; `synthesizer.backbone._no_single_point_of_failure` is what refuses to drop a circuit whose loss would leave such a city where none stood before; and `synthesizer.validation.diverse_path_count` is what counts the circuits out of a site that no single city's loss takes two of. `synthesizer.backbone.augment_physical_resilience` was the pass that hunted for these cities and added a circuit around each until GitHub issue #60 retired it on 2026-08-17, so a reader meeting that name in text written before then is meeting a function that is not on disk.

### Identifiers are spelled in these words too

#### An identifier spelled with a banned word gets renamed

The identifiers follow this too. A function called `diverse_mesh_routes` beside prose about circuits is the same synonym problem one layer down, and worse there, because a reader who greps for the word they were given finds nothing. Where a name in `src/`, `lib/python/`, `scripts/` or `test/` uses a word this note bans, the name is wrong and gets renamed. GitHub issue #61 carried the mapping and renamed what was on disk on 2026-08-17, when path was the required word: `diverse_mesh_routes` became `diverse_mesh_paths`, `routes_per_peer` became `paths_per_peer`, `max_backup_route_multiple` became `max_backup_path_multiple`, and the 70 test functions named for routes and spans were named for paths and fiber segments. That rename stands as the example of the rule even though the word it moved to is now the banned one, because the reason it was made does not depend on which word won. It also leaves most of the names in `src/`, `lib/python/` and `test/` spelled with the banned word today — `AccessPath`, `SynthesisPath` and the `drawn_paths` field on `Synthesis` in `synthesizer.model`, `synthesizer.ceiling.paths_per_peer` and `independent_paths`, `synthesizer.validation.diverse_path_count`, `max_backup_path_multiple` — and they are renamed in turn. Until a given name is renamed it is still written exactly as it is spelled, because a wrong name costs more than an inconsistent one, so quote a name that has not been renamed yet as it is spelled and say circuit in the sentence around it.

#### Names a caller already sees keep their word

Names a caller already sees are the exception, and they keep the word until somebody deliberately changes the API. The published `paths` collection, the `number_of_diverse_paths` key every tenant's `etc/*.yml` sets, and the `ValidationReport` keys are read by people outside this repository, who did not read this note and whose code breaks when a key is spelled differently. This is the same carve-out that left `backbone-links` and `link_kind` alone when "link" was banned.

#### Old text is left alone

Much of the text already on disk says path, and the issue text older than 2026-08-17 says route, span and circuit in the senses this note has since moved around. Match this rule rather than the paragraph next to you, and leave old text alone unless the file is being changed for some other reason.

### Peers and diverse circuits are different things

Peers and diverse circuits are different things, and keeping them apart is not pedantry — conflating them is the defect in GitHub issue #59. `number_of_diverse_paths` in a tenant's `etc/*.yml` is how many ways out of a site the operator is asking for. Nothing hands that number out as peer slots any more. `synthesizer.survivable.select_fiber` selects the fiber for the whole synthesis at once, so that every backbone node holds that many ways out no one city's loss takes two of, and `synthesizer.backbone._ways_out_of` then reads a site's circuits off the fiber that was selected, by calling `synthesizer.ceiling.independent_paths` over it and keeping the tenant's number of the shortest. Which peers a site ends up joined to is what falls out of that reading rather than what is decided before it. Until GitHub issue #60 on 2026-08-17 the number was spent as peer slots by `synthesizer.backbone.select_backbone_mesh_pairs`, each site reaching for that many peers, and the two words were exactly as easy to confuse then as now — the change is where the number is answered, not what it means. How many circuits one pair of sites is drawn with is still a separate question, answered by `synthesizer.ceiling.paths_per_peer`, and the answer is one unless there are too few peers to reach. A site's diverse circuits are the circuits out of it that no single city's loss takes two of — so two peers reached over one shared transit city are one diverse circuit, and two circuits to the same peer over city-disjoint fiber are two.

### Say the word for the thing

#### Do not say cable or span

Do not say "cable" or "span". The thing both reach for is a fiber segment: one length of fiber between two adjacent points, which is a `FiberSegment` in `synthesizer.input_graph` and an entry of the published `fiber-segments` collection. A circuit rides many fiber segments, so "Ashburn has four cables" says nothing a reader can act on — four fiber segments and four circuits are different numbers and only one of them was meant. The same went for "link", which is settled in its own paragraph below.

#### Do not say design

Do not say "design". What this program does is synthesize a WAN, and what it hands back is a synthesis: the seated backbone nodes, the fiber selected between them, the circuits drawn over that fiber, and the access nodes homed in. "Design" reads as a thing a person sat down and drew, which is the opposite of what happens — a solver is handed the PoPs and fiber segments and a tenant's requirements and computes the answer. It was the word throughout the repository until GitHub issue #69 on 2026-08-19, which renamed all 1,699 uses: `Design` is `Synthesis`, `DesignParams` is `SynthesisParams`, `design_payload` is `synthesis_payload`, `published_design` is `published_synthesis`, the module `lib/python/test_published_designs/` is `lib/python/test_published_syntheses/`, and the one place the word reached a caller — the `total_design_miles` key in the body `GET /wan-synthesizer/tenants/{tenant}/wan` serves — is `total_synthesis_miles`.

#### Do not say link

Do not say "link" for anything. It was the worst of these words because it was not a synonym for one thing but one word covering four, so a reader told a site holds four links could not tell whether four fiber segments, four circuits, four homings or four operator instructions were meant, and the four are different numbers. Say the word for the thing: a fiber segment for one length of fiber, a circuit for one way from one site to another, an access circuit for a tenant site or provider region homing into its backbone node, and a forced or removed circuit for what an operator instructs. How many backbone nodes an access node homes into is a homing degree and not a link at all. GitHub issue #136 renamed all of it on 2026-08-22 — 230 uses in `src/` and 472 in `test/` and `lib/python/` — so `input_graph.link_key` is `segment_key`, `graphs.path_link_keys` is `path_segment_keys`, `model.LINK_FOR_TARGET` and `model.LINK_FOR_PIN` are `PATH_FOR_TARGET` and `PATH_FOR_PIN`, `validation.node_mesh_links` is `mesh_paths_out_of`, `model.OperatorLinks`, `ForcedLinks` and `NamedLink` are `OperatorPaths`, `ForcedPaths` and `NamedPath`, and `Tuning.access_backbone_links` is `access_homing_degree`, which reads the same as the `access-homing-degree` resource it is read from. Those names are spelled with the word this note now bans and are renamed in turn; until each one is, write it exactly as it is spelled. Three names keep "link" because a caller already sees them: the published `backbone-links` collection served at `/wan-synthesizer/tenants/{tenant}/backbone-links`, whose entries are circuits; the `link_kind` field of each entry of the published `paths` collection; and the four keys of `ValidationReport` that spell it, `backbone_mesh_survives_any_one_link_loss` among them. Write those exactly as they are spelled and say circuit or fiber segment in the sentence around them.

#### Do not say path

Do not say "path". It is the graph theorist's word for the thing, and the people who read this repository are network engineers who already have their own: what they order from a carrier, hold, and pay for every month is a circuit. Saying path asks them to translate on every line, and using it beside circuit splits one thing into two, so a reader who has just been told a pair holds two circuits cannot tell whether the two paths mentioned in the next paragraph are the same two or two more. This note said the reverse until 2026-08-22 — it banned circuit and required path, on the argument that a synonym splits one thing in two. That argument was right and is why only one word is allowed; it decided nothing about which of the two wins, and the word the reader already owns is the one that wins. Say circuit.

#### Do not say route

Do not say "route" either, even though it means the right thing. It is the harm a synonym does rather than the harm a wrong word does: a reader met with circuit in one paragraph and route in the next has to stop and work out whether the same thing is meant. Say circuit every time.

### Sites, backbone nodes and access nodes

Carrier PoPs, tenant sites, provider regions and off-net sites are all sites, and there are two kinds. A backbone node is a site the mesh seats in the backbone tier — a carrier PoP at a data-center city, listed in the published `backbone-nodes` collection and capped by `backbone.node_count.max` in the tenant's `etc/*.yml`. An access node is a site that homes into the backbone rather than meshing: a tenant site or a provider region, joined to its backbone node by an `AccessPath` in `synthesizer.model` and listed in the published `tenant-nodes` and `provider-nodes` collections. Say which kind whenever the sentence turns on it, because almost every rule in the synthesizer applies to one kind and not the other. "Site" on its own is right when the sentence is true of both, or when the PoPs and fiber segments are what is being discussed rather than the synthesis. Write "node" only as "backbone node" or "access node", never on its own: a bare `node` in an identifier is how this goes wrong, because it says neither which kind is meant nor that either kind is required, and it is the graph-theory word where the network word already exists. GitHub issue #134 renamed the bare ones on 2026-08-22 — 119 in `src/` and 45 in `test/` and `lib/python/`, in `synthesizer.ceiling`, `synthesizer.validation`, `synthesizer.graphs`, `synthesizer.assemble`, `synthesizer.coverage` and `synthesizer.backbone` — and renamed `synthesizer.codec._place` and `_load_places`, a third word for the same thing, to `_site` and `_load_sites`. `backbone_nodes`, `access_node` and the tenant config key `backbone.node_count.max` keep the word, because each of them says which kind is meant.

### There is no map

There is no map: the word means only the carriers' published network maps in `data/raw/`, which no code opens, and what the synthesizer is given is the PoPs, fiber segments, tenant sites, provider regions and off-net sites that `scripts/seed.py` PUTs into S3 from the CSV files under `data/`.

### Which word for which thing

Which word for which thing, when precision is needed:

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

## Notes

This was written on 2026-08-17, after a question about Minuteman's Ashburn, VA — why a site asking for two diverse circuits had four — was answered twice in the wrong words. The first answer counted cables, which meant nothing on circuits crossing nine cities each. The second used peer and diverse circuit as though they were one thing, which hid the actual defect: Ashburn held three peers and four circuits, because one pair was drawn twice. Naming those two separately is what made the defect visible, and `synthesizer.ceiling.paths_per_peer` — how many of a site's ways out one peer is allowed to take, which is one unless there are fewer peers to reach than the site was asked for circuits — is a rule that cannot even be stated without both words. The rule quoted here until GitHub issue #60 was `backbone.restore_diverse_paths`, a second circuit between two sites drawn only where the fiber left one of them no other way out; that pass was retired on 2026-08-17 and its name is no longer on disk, but it made the same point. The rest of the list was settled the same day, one correction at a time, as each substitute word turned up in an answer and had to be asked about again. Circuit replaced path on 2026-08-22, which is the one entry in the list that was settled twice.

The telecom vocabulary this sits inside — circuit diversity rather than mesh degree — is in [how-issues-are-written](how-issues-are-written.md), which requires it of issues; this note requires the same words everywhere else. Naming the function, file and config key rather than describing them is [write-the-exact-name](write-the-exact-name.md).
