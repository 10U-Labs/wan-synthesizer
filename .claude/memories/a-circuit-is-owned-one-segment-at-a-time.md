---
name: a-circuit-is-owned-one-segment-at-a-time
description: "A fiber segment is one carrier's when it has a PoP at both ends, and a circuit may run over any number of carriers' segments in turn, handing off at a PoP both have; the code still holds a circuit to one carrier end to end, which GitHub issue #170 is about"
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

**How to apply:** The program holds the stricter rule — one carrier's fiber end
to end — in `stages.finalize` (`adjacency_by_carrier`), the drawing in
`backbone` and `survivable`, `SynthesisCircuit.carrier`, and six tests named in
GitHub issue #170. That is the defect, not the rule. Do not restate the
one-carrier rule in a new test or a new issue; a circuit's carrier is a
per-segment fact and `FiberSegment.carriers` already holds it. #170 is blocked
on #187, which puts dcn's six out-of-state landings in `data/pops/dcn.csv` so
dcn owns its exits on the stated rule. See
[[a-way-out-of-a-site-is-a-circuit]].
