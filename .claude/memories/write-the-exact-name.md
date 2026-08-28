# Write the exact name

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A line number is not a name](#a-line-number-is-not-a-name)
  - [Coined collective nouns are the common failure](#coined-collective-nouns-are-the-common-failure)
  - [Precision and simplicity are both required](#precision-and-simplicity-are-both-required)
  - [Verify a name, and prefer a table for several](#verify-a-name-and-prefer-a-table-for-several)

## Overview

Every noun that has a name in the repository is written by that name, everywhere — chat replies, issue and pull-request bodies, commit messages, and these notes. A name is a thing the reader can open: a path, a function, class, constant or field with the file it lives in, an S3 object key, a workflow file, a config key, an endpoint and its method. When a phrase cannot be pasted into a search box and land somewhere, it is not naming anything, and the reader has to reconstruct what was meant from context the writer had and they do not.

## Conventions

### A line number is not a name

The next commit moves it and nothing says when. It goes in one place only: a `::error file=,line=::` annotation, which is generated against the commit being checked and read minutes later against that same commit, so it cannot go stale. `_ways_out_of` in `backbone.py` and `backbone.py:220` tell the reader the same thing, except that a reader can grep the first and it keeps being true. One commit that deleted prose and changed no behaviour left not one of 32 stored line references pointing where it had, and four of them had pointed at blank lines, which cannot be re-derived at all.

### Coined collective nouns are the common failure

"The layer", "the machinery", "the pipeline", "the store", "the far side" all read as though they refer to a known thing, which is what makes them worse than saying nothing: the reader assumes the term is repository vocabulary they are supposed to recognise, goes looking for it, and finds it nowhere. Say the directory, the module, the bucket, the object key. Where a group genuinely has no name, name its members once and then use a term defined in that sentence.

### Precision and simplicity are both required

Simple English means short sentences and no computer-science jargon where a plain word will do; it does not license a vague noun. Precision means the exact identifier; it does not license a wall of qualifiers. "One function is wrong: `settled`, in `lib/python/test_published_syntheses/__init__.py`" is both. "The delivered-synthesis layer waits on two of the eight backbone knobs" is neither. That model sentence is the right way to name a function and the wrong way to open an issue: a plain sentence saying what the thing is and what it is for comes before the first identifier.

### Verify a name, and prefer a table for several

Prefer a table when several named things each have several properties, so the reader can look one up rather than hold eight of them in their head. Verify a name before writing it: workflow files are not named after the directories they test, a function moves between modules, and a wrong name costs more than a vague one because it sends the reader somewhere real and wrong.
