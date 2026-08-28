# Lead with what it is for

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Cut a correct detail that changes nothing](#cut-a-correct-detail-that-changes-nothing)
  - [Explain why a thing exists by what changes and what does not](#explain-why-a-thing-exists-by-what-changes-and-what-does-not)
  - [Name it after the sentence saying what it is](#name-it-after-the-sentence-saying-what-it-is)
  - [No analogies](#no-analogies)
  - [Say what it costs near the top](#say-what-it-costs-near-the-top)

## Overview

Every paragraph opens with a plain sentence saying what the thing is and what it is for. The identifiers come after that sentence. This holds in chat replies, issue and pull-request bodies, commit messages and these notes, and it holds section by section rather than once at the top. Assume the reader has not opened the files and will not open them while reading.

## Conventions

### Cut a correct detail that changes nothing

A detail earns its place by changing what somebody would do, and moves later or goes when it does not. A table of the eight `backbone` keys against the four places each reaches is the right shape for that question and still lands as a wall when it arrives before the reader knows why eight keys matter. Cutting a correct detail is not vagueness. Replacing it with a coined noun is.

### Explain why a thing exists by what changes and what does not

A reader asking why some value has to be there at all is not helped by what it is called, what type it has, or where it is passed. Say what the program is doing at that moment, in one sentence. Then what that step requires, as a short list of facts in the reader's own vocabulary. Then the thing about those facts that forces the design, which is usually that some of them change and some do not. Nothing in that says what the value is called, and a reader reaches the end able to say what it is for.

### Name it after the sentence saying what it is

Telling a reader that `settled`, in `lib/python/test_published_syntheses/__init__.py`, decides when a tenant's build has stopped moving tells them nothing until they know that anything waits, what it waits for, and why. Say that first: the tests can read `tenants/daf/wan.json` before the synthesizer Lambda has rewritten it, so `delivered_syntheses_fixture` sleeps until the rewrite lands. Then name the function that decides when to stop sleeping. The names are owed either way; the order decides whether the reader can use them.

### No analogies

A comparison to something outside the repository asks the reader to accept that two things are alike when they cannot check it, and swaps the vocabulary they are trying to learn for vocabulary from somewhere else. Say the PoPs, the fiber segments, the tenant's configuration and the miles. Keep the sentences short and put one fact in each.

### Say what it costs near the top

"The workflow goes green and reports that the published networks match the configs, and that green cannot be told apart from a real one" is what a reader needs in order to care about the eight keys. It belongs in the first few lines, not the seventh paragraph.
