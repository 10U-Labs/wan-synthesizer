---
name: a-chosen-carrier-pop-is-a-wan-pop
description: "A carrier PoP the synthesis chooses is a wan_pop and the verb for choosing it is select, backbone survives only where it names the mesh itself, and node survives only in two graph-algorithm types"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9e8f1661-2c5f-4af0-a435-4ed41520ab15
  modified: 2026-09-11T01:11:53.788Z
---

# A chosen carrier PoP is a WAN PoP

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [The word is wan_pop, everywhere a PoP is meant](#the-word-is-wan_pop-everywhere-a-pop-is-meant)
  - [The verb is select, not seat](#the-verb-is-select-not-seat)
  - [Where backbone survives](#where-backbone-survives)
  - [Where node survives](#where-node-survives)
  - [What this cost on the wire](#what-this-cost-on-the-wire)
  - [Nothing mechanical checks this](#nothing-mechanical-checks-this)

## Overview

The synthesizer's central decision is which of the carriers' PoPs a tenant's WAN
runs through. An offered one is a `carrier_pop`; a chosen one is a **`wan_pop`**;
one a circuit merely crosses is a `transit_pop`. The three share a word on
purpose, because the whole of the difference between them is which ones the
synthesis chose, and a reader who cannot see that from the names cannot follow
the program's subject. GitHub issue #147 settled this on 2026-09-10, against
`backbone_node`, which shared no word with the `carrier_pop` it is one of.

`wan_pop` was chosen over `backbone_pop` by the operator, knowingly: it reads as
*a PoP the WAN runs through*, which CLAUDE.md's second clause says a transit PoP
also is, so `wan_pop` and `transit_pop` overlap in a way `backbone_pop` and
`transit_pop` would not have. What separates them in the code is that a
`wan_pop` is selected from the tenant's inputs and a `transit_pop` is not.

## Conventions

### The word is wan_pop, everywhere a PoP is meant

`Synthesis.wan_pop_ids`, `SynthesisParams.min_wan_pop_count` /
`max_wan_pop_count` / `forced_wan_pop_names` / `degree_exempt_wan_pop_names`,
`RoleOverrides.forced_wan_pop_ids` and its two siblings,
`ForcedCircuits.required_wan_pops`, `SynthesisInputs.eligible_wan_pop_ids`,
`_SearchPlan.wan_pop_candidates`, `WanPopConstraints`, `wan_pop_strength`,
`collections.wan_pops`, the `"wan_pop"` value of a site's `tier_role`, and the
`WAN PoP` the SPA prints under a purple dot. CLAUDE.md says WAN PoP too, and its
heading is **The per-PoP ask**.

### The verb is select, not seat

The synthesizer makes two choices and they are one operation over two kinds of
thing: which carrier PoPs the WAN runs through, and which fiber segments its
circuits run over. Both are **selection**. The fiber side already said so —
`survivable.select_fiber` returns a `FiberSelection` built from a
`SegmentSelection`, and `backbone._Drawn` holds `selected` and
`selected_by_carrier` — and the PoP side already spoke the first half of the
pair, in `_SearchPlan.wan_pop_candidates`, `SynthesisInputs.eligible_wan_pop_ids`
and `strength`'s `candidate_ids`. The word that completes *candidate* is
*selected*.

`seat` was the second verb for the PoP half, and it resolved no ambiguity that
naming the object does not. This repository had already settled that question
once: the served `paths` collection became `/homing-circuits` and
`/fiber-segments` because it held both and no one word is true of both — see
[a-way-out-of-a-site-is-a-circuit](a-way-out-of-a-site-is-a-circuit.md). The same
answer holds here, so `select_fiber` and `select_wan_pops` need no third word
between them.

`seat` was also a second **noun** for a `wan_pop`, and it pointed at the wrong
object. A seat reads as a slot inside a facility, which is the resolution
[a-site-is-a-named-place-not-a-building](a-site-is-a-named-place-not-a-building.md)
says this program does not model. A capped WAN PoP was never the WAN being sold one
slot in a Minot facility; it is the merged carriers' fiber out of the *city* of
Minot carrying one diverse circuit.

The operator settled this on 2026-09-11 and CLAUDE.md changed first, the way
GitHub issue #147 established a directive word has to: the prime directive read
"the WAN PoPs a tenant's inputs **seat**" and now reads **select**, and its
`access nodes` became "the sites that home into them", taking the words GitHub
issue #161 settled when `/tenant-nodes` and `/provider-nodes` became
`/tenant-sites` and `/provider-regions`.

**The code has moved.** GitHub issue #186 closed this on 2026-09-11 and `seat`
now appears nowhere outside the city of Seattle. The knob `seat_cap` took the
published name it is assigned from, `max_wan_pop_count`, through `search_plan`,
`backbone`, `survivable`, `ceiling` and `test_published_syntheses`; the nouns
became `validation.capped_wan_pops`, `circuits_clear_of_a_capped_wan_pop` and
`survivable._wan_pops_the_carriers_can_give_two_circuits`; the verbs at
`synthesize.py:59`, `synthesize.py:290`, `validation.py:299` and
`coverage.py:152` became *select*; and `offnet.SeatedOffNetSites` became
`RealizedOffNetSites` carrying `off_net_ids`, taking its shape from the sibling
`on_net_fabrication.FabricatedOnNetPops` and its `on_net_ids` that
`stages.dual_home` calls beside it. Off-net prose took `codec.OFF_NET_KIND`'s word
*site* rather than *select*, because building a local-fiber twin is not the
selection the directive names.

No published resource name moved — the five hits in `openapi.json` were prose
inside `summary` and `description` — so it was a read-and-rename commit rather
than a re-seed. One test name was written rather than substituted:
`test_no_synthesis_stopped_short_of_its_target_with_a_seat_left_to_spend` was
built on the countable-slot sense, and it is now
`test_no_synthesis_missed_its_coverage_target_below_the_wan_pops_it_was_allowed`,
which is what it asserts.

### Where backbone survives

`backbone` still names **the mesh those PoPs form, and the tier demand sites
home into** — never a PoP. It survives in `synthesizer.backbone`, `BackboneMesh`,
`backbone_mesh` as a circuit's `purpose`, `backbone_lower_bound_miles`, the
`tenant_to_backbone` and `provider_to_backbone` kinds, every `backbone_*` key of
the served validation report, the `backbone` and `removed_backbone` fields of
`OperatorCircuits` and `ForcedCircuits` with the `forced_backbone_pairs` and
`removed_backbone_pairs` helpers that read them, the served `backbone-circuits`
collection, and the `backbone:` block of each `etc/*.yml` with the two knobs
named for it — `backbone_coverage_target_miles` and
`backbone_number_of_diverse_circuits`, the latter also a published resource.
A candidate set is still a backbone, so `backbone_set` went to `wan_pop_set` but
`meshed_backbone_synthesis` and `split_backbone_synthesis` did not.

### Where node survives

Twice, both of them graph algorithms rather than networks: `_Node` and its
`_Residual`, `_Costs` and `_Arc` companions in `synthesizer.ceiling`, which are
vertices of a unit-capacity flow network, and the `ast` nodes
`scripts/assert_description_names_what_exists.py` walks. The same exemption
`reconstruct_path` and `_augmenting_path` hold for `path` — see
[a-way-out-of-a-site-is-a-circuit](a-way-out-of-a-site-is-a-circuit.md). The two
served collections `/tenant-nodes` and `/provider-nodes` still say it and are
wrong under any answer, because a tenant's site is not a PoP at all; that is
GitHub issue #161 and it is open.

### What this cost on the wire

Five published resources were renamed and every caller has to move:
`backbone-nodes` → `wan-pops`, `forced-backbone-nodes` → `forced-wan-pops`,
`prohibited-backbone-nodes` → `prohibited-wan-pops`,
`degree-exempt-backbone-nodes` → `degree-exempt-wan-pops`, and
`backbone-node-count` → `wan-pop-count`. The last four are also object keys under
`tenants/{tenant}/` in the store and keys in `etc/`, so the migration is a
re-seed: `push_tenants` PUTs the new keys, `TENANT_FILES` in the store handler no
longer lists the old ones, and `prune_store` deletes them on the same run. The
`etc/` keys moved with them — `backbone.forced.wan_pops`,
`backbone.prohibited.wan_pops`, `backbone.wan_pop_count`, and the `settings` keys
`wan_pop_search_memory_share` and `bytes_per_wan_pop_combination`. One tenant was
named for the word: `etc/two_node.yml` became `etc/two_pop.yml`, label `Two-PoP`,
tenant id `two-pop`, with `data/tenants/two_pop.csv` beside it, so `prune_tenants`
deletes the old `two-node` tenant on the next seed.

### Nothing mechanical checks this

No job reads this file and no tier can fail on a word, for the reason
[why-static-analysis-is-asked-separately](why-static-analysis-is-asked-separately.md)
gives: a tier runs the program and judges what comes back, and which word an
identifier uses is not something a running program produces. Recording the
settled words somewhere a job can open is GitHub issue #158, and a check that the
five hand-written lists of resource names agree is GitHub issue #159. Both are
open, so this rename is held only by whoever reads next.
