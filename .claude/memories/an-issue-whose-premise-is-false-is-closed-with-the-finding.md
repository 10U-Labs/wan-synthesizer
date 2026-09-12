---
name: an-issue-whose-premise-is-false-is-closed-with-the-finding
description: "An issue whose defect cannot occur is closed by a comment carrying the argument and the measurement, not by a behaviour-identical refactor with a test that cannot fail"
metadata:
  type: feedback
---

# An issue whose premise is false is closed with the finding

An issue that describes a defect the code cannot produce is closed with a
comment giving the argument and the measurement, and no commit. The
behaviour-identical refactor the issue proposes is not made, because the test
that would go red first does not exist, and a test that is green before and
after is the check CLAUDE.md says is worth nothing.

**Why:** GitHub issue #171 held that `_relieved` gives up on a PoP whose cut a
later circuit could regroup. Adding fiber only merges components of the mesh
with that PoP removed, so the pairs across it only shrink and a refused PoP is
refused on every later mesh; the seven seeded tenants gave identical circuit
lists under both loops. The user chose closing with the finding over the
refactor.

**How to apply:** before authoring the red test an issue calls for, check that
the defect can happen — by argument over the code, and by
[measure-a-change-over-the-seeded-tenants](measure-a-change-over-the-seeded-tenants.md)
where a run settles it. If it cannot, `gh issue close N --comment` with the
argument and the figures, reason `not planned`. This is the one case
[an-issue-is-closed-by-its-commit](an-issue-is-closed-by-its-commit.md) does not
reach, since there is no commit to carry the line.
