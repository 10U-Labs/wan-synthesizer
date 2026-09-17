---
name: the-over-water-rule-holds-one-hop-at-a-time
description: "A crossing never arrives on the shore its hop started from, and that is the whole of the over-water rule; a WAN spanning two shores is joined the long way round through a PoP across the water, so no floor row asks two circuits over land of a pair"
metadata:
  type: project
---

# The over-water rule holds one hop at a time

The rule is about one drawn circuit: a circuit between two WAN PoPs on the
same shore runs over land, and a circuit to a PoP across the water crosses
once and stays there, which `ceiling._without_crossings_home` proves by
dropping every submarine arc that arrives on the shore the site stands on
and keeping the rest. `test_no_published_pair_joined_over_land_is_drawn_a_circuit_under_water`
holds the published circuits to it, pair by pair.

It is not a rule about the two circuits the directive asks between every
pair. A pair joined over land is two-vertex-connected the long way round
when the WAN has PoPs across the water: DAF's Cheyenne and Ashburn hold one
way over land and one through Atlanta, Molesworth and Stuttgart, and each
hop of that way is a legal circuit. Issue #238 was the floor asking DAF's
every US pair two circuits over land and each European PoP two over
European land, rows nothing published answered, so the published miles sat
8.867 under the floor for every seed since 7c3ce2b.

**Why:** the floor is the one published figure the directive costs, and a
relaxation over rows the circuits are not held to is not a floor. The
directive says nothing about which of a pair's two circuits runs over land.

**How to apply:** `survivable` writes every row over the whole fiber and
bars arcs, through `SeparationQuestion.barred`, rather than dropping
segments. A PoP's own row bars every crossing arriving on its shore, which
is the ceiling's network exactly. A pair row bars those same arcs only when
every WAN PoP stands on the near PoP's shore, since then every hop starts
there; a WAN on two shores bars nothing between a pair. A WAN whose only way
round a PoP is under water to a transit PoP on an island and back is still
refused as split, because that hop arrives back on the shore it left.
The synthesizer and the measurement of its tenants live in
`10U-Labs/api.10ulabs.com` since the API migration.
