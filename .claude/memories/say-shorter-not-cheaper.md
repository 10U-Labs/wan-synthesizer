# Say shorter, not cheaper

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Cost inside synthesizer.ceiling stays](#cost-inside-synthesizerceiling-stays)
  - [Money is a fact about operators, never a number about a synthesis](#money-is-a-fact-about-operators-never-a-number-about-a-synthesis)
  - [Say selected, never bought or sold](#say-selected-never-bought-or-sold)

## Overview

Nothing in this repository records money: no price, no tariff, no monthly charge and no currency in `src/`, `lib/`, `etc/` or `data/`. Every number the synthesizer computes, compares or publishes is a distance in miles. So say shorter, or the fewest fiber miles. "The cheapest circuit" claims the synthesis compared two prices, and it did not — and the wrong word sends a reader looking for where the prices are configured, which they will not find and cannot then tell apart from an oversight.

## Conventions

### Cost inside synthesizer.ceiling stays

Its minimum-cost maximum flow measures cost in miles, which the code says for itself: `_add_capacity` in `ceiling.py` unpacks each new arc as `tail, head, miles, units`. Inside that module, cost, cheapest and refund are the algorithm's own words for mileage. What must not happen is the word leaking out into prose about a finished synthesis, where nobody has told the reader that cost means miles.

### Money is a fact about operators, never a number about a synthesis

An operator pays for every circuit they hold, which is why an unneeded circuit is a defect worth an issue rather than a harmless extra. What is not allowed is comparing two circuits by price, calling one option the expensive one, or claiming a change saves money. Say what it saves in miles and give the figure. An operator orders a circuit from one carrier end to end and pays for it every month, and a carrier offers one: the rule is about the program, which has no money in it, not about the people it serves.

### Say selected, never bought or sold

"Cheapest" claims a comparison the program did not make; "buy" claims a transaction it has no notion of at all. The program **selects** fiber segments: `synthesizer.linear_program` answers in fractions, and each round of `synthesizer.survivable._round_up` selects outright every segment that answer holds at half or more. A carrier does not sell fiber either — it offers it, and the whole of what the code does with `FiberSegment.carriers` is ask whether one company has fiber the whole way along a circuit.

Selection names a second decision, so say which one: `backbone_nodes` in `collections.py` reads back the carrier PoPs a synthesis seats, which is selecting sites rather than fiber. Three substitutes are taken by names already on disk and cannot stand in: `taken`, because take means a loss taking two of a site's circuits; `held`, because `SegmentSelection.held` is how much of a segment the answer holds; and `ordered`, because `_Search.order` is the column order.
