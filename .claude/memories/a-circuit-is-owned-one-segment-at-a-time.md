---
name: a-circuit-is-owned-one-segment-at-a-time
description: "A fiber segment is one carrier's when it has a PoP at both ends, and a circuit may run over any number of carriers' segments in turn, handing off at a PoP both have; the synthesizer proves, selects and draws circuits over the merged fiber for exactly that reason, and no one-carrier-per-circuit rule may be restated"
metadata: 
  node_type: memory
  type: project
  originSessionId: b6f7d5dc-8da8-4c5a-90e0-2e9edf98a065
  modified: 2026-09-12T02:53:08.017Z
---

# A circuit is owned one segment at a time

A fiber segment belongs to a carrier when that carrier has a PoP at both of its
ends. A circuit is any sequence of such segments, and it may change carrier at
any PoP two carriers share, as many times as it needs to. What is not a circuit
is a sequence with a segment nobody owns — `a` a zayo PoP, `b` a dcn PoP, `c` a
zayo PoP, with no carrier at both ends of `a` to `b`.

**Why:** Under the Telecommunications Act a local exchange carrier must sell its
services to another carrier at a set price, so zayo can sell Minot → Chicago →
Ashburn, buying the Minot → Chicago stretch from dcn. The rule the user stated
on 2026-09-11 is per segment, not per circuit.

**How to apply:** The program holds this rule by proving, selecting and drawing
circuits over the merged fiber and nothing else: `ceiling.CircuitProofInputs`
takes one adjacency, `survivable.FiberInputs` one fiber map, `backbone` one
Dijkstra per pin, and `SynthesisCircuit` names no carrier because a circuit has
none — `FiberSegment.carriers` holds the fact per segment, where it belongs. The
per-carrier machinery (`adjacency_by_carrier`, `carriers_along`,
`SynthesisCircuit.carrier`, the capped-WAN-PoP exemption in
`validation.backbone_mesh_cut_pops` and the e2e grader) went with GitHub issue
#170 on 2026-09-11, after #187 put dcn's six out-of-state landings in
`data/pops/dcn.csv` so dcn owns its exits on the stated rule. A WAN PoP the fiber
caps below two circuits is now refused by `stages.finalize` as a split, not
quietly dropped from the cut-PoP check. Do not restate the one-carrier rule in a
new test, a new issue or a new field; a circuit that changes hands at a PoP both
carriers have is a circuit. uniti still lists sixteen segments ending at cities
its PoP file does not carry — #187 named that the same defect and left it open.
See [[a-way-out-of-a-site-is-a-circuit]].
