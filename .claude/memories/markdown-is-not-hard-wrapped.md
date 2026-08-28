# Markdown is not hard-wrapped

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Hard wrapping costs a reflow on every edit](#hard-wrapping-costs-a-reflow-on-every-edit)
  - [Nothing enforces a width](#nothing-enforces-a-width)
  - [The trap is the files already on disk](#the-trap-is-the-files-already-on-disk)

## Overview

There is no column limit on markdown in this repository, and none on the markdown written into GitHub issues and pull requests either. Write a paragraph as one line and let whatever displays it do the wrapping. Do not break a sentence across lines to hit 72, 80 or any other width.

## Conventions

### Hard wrapping costs a reflow on every edit

An edit to the middle of a wrapped paragraph reflows every line after it, so a one-word change shows up as a rewritten block and the real change hides inside the noise. Unwrapped, a paragraph edit touches one line.

### Nothing enforces a width

`documentation.yml` runs `markdownlint` with `--disable MD013`, MD013 being the line-length rule, and every workflow that lints YAML sets `line-length: disable` before it runs. A hard-wrapped paragraph therefore passes CI exactly as an unwrapped one does; the choice is a convention, and the convention is not to wrap.

### The trap is the files already on disk

Most of the markdown here was written hard-wrapped before the restriction was lifted, so imitating what is already on disk reproduces the old style. Take the width from this note, not from the neighbouring file.
