---
name: the-store-holds-only-what-the-product-writes
description: "The store bucket has no working area: every key under a prefix the prune does not know is deleted on the next seed, so scratch state has nowhere to live there"
metadata:
  type: project
---

# The store holds only what the product writes

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [There is no working area](#there-is-no-working-area)
  - [What this costs a future prefix](#what-this-costs-a-future-prefix)
  - [A delete names the null version](#a-delete-names-the-null-version)

## Overview

`wan-synthesizer-store-us-east-2` holds the carriers' PoPs and fiber, the
providers' regions, each tenant's operator inputs, and the `wan.json` and
`wan-status.json` the synthesizer publishes. `POST /wan-synthesizer/store/prune`
deletes everything else, and `is_current` in
`src/api/common/storage/lambdas/handler.py` is the whole of the rule:
`_KEPT_BY_PREFIX` names one set of file names per prefix, and a prefix that set
has never heard of goes whole.

## Conventions

### There is no working area

`_WORKING_PREFIXES = ("source/", "builds/")` used to exempt two prefixes from
that rule. Nothing in the repository ever wrote to either, and on 2026-09-11 the
live bucket held 141 objects under `carriers/`, `providers/` and `tenants/` and
none at all under the two exempt names. So the exemption could not fire, the
bucket's `expire-build-artifacts` lifecycle rule expired objects that were never
created, and GitHub issue #165's migration -- new prefix written, old objects
stranded -- had nothing to migrate. Both went, which is what closed #165 rather
than the rename it proposed. `builds/` was also the wrong verb: this program
synthesizes, it does not build, which is what GitHub issue #124 says about the
six places the word is only text.

### What this costs a future prefix

Adding a prefix to the store now means adding it to `_KEPT_BY_PREFIX` in the
same commit. A writer that lands first puts its objects somewhere the prune
takes them out on the next `seed` run, and the seed runs on every push -- see
[seed-tests-every-push](seed-tests-every-push.md). `GET` on the same route names
what would go without touching it, so an operator can look first.

### A delete names the null version

The bucket's versioning is Suspended, and under suspended versioning a
`delete_object` that names no `VersionId` does not remove the key: it takes
out the null version and writes a null delete marker in its place, which
`get_object` and `list_objects_v2` hide and `list_object_versions` goes on
listing. Every delete against the store passes `VersionId="null"`, and the role
behind it holds `s3:DeleteObjectVersion` beside `s3:DeleteObject`, because
naming a version is a different permission. GitHub issue #178 is what one
delete without it cost: the `seed` run that retired the `two-node` tenant left
a marker over each of its sixteen objects, and
`test_no_delete_marker_is_left_behind` was red on every storage run after it
with nothing in the repository able to clear one. The prune now pages
`list_object_versions` and removes every marker it lists, so a marker that
does appear is gone on the next `seed` run, and a new writer that deletes
without the version is caught by the fake in `lib/python/test_s3_store_mock`,
which models the marker.
