# Code names say what the thing is

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Abbreviations only where the abbreviation is the ordinary form](#abbreviations-only-where-the-abbreviation-is-the-ordinary-form)
  - [Filler nouns distinguish nothing](#filler-nouns-distinguish-nothing)
  - [Name the thing the thing is](#name-the-thing-the-thing-is)
  - [Prefer the network engineer word to the computer scientist one](#prefer-the-network-engineer-word-to-the-computer-scientist-one)
  - [Two checks that catch most of it](#two-checks-that-catch-most-of-it)

## Overview

A name in the code is read far more often than it is written, and almost always by somebody who has not opened its definition and is not going to. So a class, function, variable or field is named such that a reader meeting it for the first time can say what it holds or does, in ordinary words, from the name alone. There are no docstrings and no comments here, so there is nobody left to explain a name that does not.

## Conventions

### Abbreviations only where the abbreviation is the ordinary form

`PoP`, `WAN` and `id` are ordinary. `cfg`, `res`, `tmp`, `idx`, `pt` and single letters are not, except as a loop variable whose whole life is two lines. Length is not the cost being minimised; a name six characters longer that removes a question is a saving.

### Filler nouns distinguish nothing

Substrate, ground, context, handle, use, spec, info, data, manager, helper, wrapper. They attach to anything, so they say nothing, and the list covers variables and parameters and fields as much as classes. Where the thing being named is a bundle of arguments rather than anything on the network, every candidate comes out saying nothing and the answer is to delete the value rather than rename it: a value built on one line and read on the next does not need a name.

### Name the thing the thing is

A class holding the sites in the backbone, the joins the operator pruned, the carrier fiber and the backup limit is named for those, not for the role it plays in somebody's mental picture of the calculation. Where a class genuinely bundles several things because they travel together, name it for what the bundle is for, in words a network engineer would use without being taught them. A field and its type must not disagree: a field holding a list of `SynthesisPath` is `drawn_paths`, because `use.path` reads as though a use had a path rather than being one.

### Prefer the network engineer word to the computer scientist one

The readers here are network engineers, so prefer the word they already have, and take the words for the parts of a backbone from [say-peers-and-circuits](say-peers-and-circuits.md) — in identifiers as well as in prose.

### Two checks that catch most of it

Read the name in a sentence saying what it is, and ask whether the name would have produced that sentence in the reader's head. Then write out the one line you would have put beside the definition when prose there was still allowed: if it and the name say the same thing the name is right, and if the line is a correction the name is wrong. Nothing mechanical checks any of this, and it applies to old code as it is touched as much as to new.
