# wan-synthesizer

## The prime directive

The synthesizer exists to synthesize **2-vertex-connected** WANs: a WAN no single city's loss can split. Equivalently, two circuits sharing no intermediate city run between every pair of cities the WAN reaches.

Every change is judged against this first. A change that tightens a floor, tidies a published figure or turns a test green while leaving a WAN a city can split has not helped.

### Where it lives

- `backbone._relieved` adds circuits until the WAN has no articulation point, whenever `number_of_diverse_circuits` is 2 or more. It reads `_DrawnFiber.whole` — the entire carrier fiber graph, not the selection — so shrinking what `select_fiber` selects does not starve it.
- `backbone._cut_cities` is `articulation_points` over the graph the drawn circuits run over, transit PoPs included, so the directive covers every city on the WAN and not only the backbone nodes.
- `backbone._needed` will not drop a circuit that reintroduces an articulation point into a WAN that had none.
- `test_no_published_network_is_split_by_the_loss_of_one_city` grades the published WAN against the directive. It is red. GitHub issue #127 is open on it.

### What the directive is not

`number_of_diverse_circuits` ways out of each backbone node is a weaker, per-node requirement. It is what `etc/` asks for, `survivable._ways_out_rows` writes down, `backbone._laid` draws, `validation.diverse_circuit_count` counts, and `stages.finalize` holds a synthesis to.

It does not imply the directive. Every backbone node can hold the circuits it is owed and a city's loss still split the WAN — which is what #127 reports. Where the two part company the directive wins, and the gap is a defect to report rather than a tolerance to widen.

### The floor is not the directive either

`backbone_lower_bound_miles` is a lower bound obtained by relaxing whichever requirement rows `survivable._requirements` writes, and it is only ever a floor for the rows actually written. It is a report card on the synthesizer, never a fact about the WAN, and never a reason to publish a WAN a city can split.

The factor-of-two result `survivable` was built around (Fleischer, Jain and Williamson 2006, on the half-integrality of Jain 2001) is proved for element connectivity, which is neither the per-node requirement nor the directive. It is not a guarantee about anything this program publishes and is not a reason to keep a requirement row. The floor itself does not rest on it — that comes from the relaxation alone, and holds for whatever rows are written.

## Conventions

The rules this repository works by are one per file under `.claude/memories/`, indexed in `.claude/memories/MEMORY.md`. Read that index first.
