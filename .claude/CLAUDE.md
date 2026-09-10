# wan-synthesizer

## The prime directive

The synthesizer exists to synthesize **2-vertex-connected** WANs.

A WAN is 2-vertex-connected when the loss of any one city it runs through leaves every remaining city still reaching every other. Equivalently: between every pair of cities the WAN reaches, two circuits run that share no intermediate city.

Every city the WAN runs through is held to this, not only the backbone nodes a tenant named. A city a circuit merely passes through is a city whose loss can split the WAN.

This is the goal. Everything else here is a means to it and is wrong wherever it does not serve it.

## What the directive outranks

**The per-node ask.** A tenant asks for a number of diverse circuits out of each backbone node. That is an input, not the goal. Every node can hold the circuits it was asked for and the loss of one city still split the WAN. Where the two disagree the directive wins, and the shortfall is a defect to report rather than a tolerance to widen.

**Every published figure.** The miles a WAN's circuits run over, the floor published beside them, and the ratio between the two are a report card on the synthesizer. None of them says whether a city's loss splits the WAN. A tighter floor is never a reason to publish a WAN that splits.

**Every imported guarantee.** A result proved elsewhere counts here only if the thing it is proved about is this directive. A guarantee about a differently stated network is not a guarantee about any WAN this program publishes, and is not a reason to state a requirement the directive does not ask for.

**Every green run.** A green run means the checks that exist passed, not that the directive is met. A check that cannot fail is worth nothing. A directive with nothing checking it is the gap to close.

## Reading this repository

The code is held to this file, not this file to the code. Where the program does something this file does not call for, the program is what is questioned first.

The conventions this repository works by are one per file under `.claude/memories/`, indexed in `.claude/memories/MEMORY.md`.
