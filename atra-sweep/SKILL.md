---
name: atra-sweep
description: >
  Autonomous entropy auditor for a project's memory layer. Detects drift between
  the code and the memory annotating it — dead links, register/inline mismatches,
  aging un-promoted scaffolds, passed gates, stale rationale, unanswered DECISION
  nodes — and emits a skimmable digest with a trend line. Built to run unattended
  (nightly cron, launchd, or a scheduled CI job) AND to surface findings in
  session. It PROPOSES fixes onto a branch and writes a report; it never commits
  to the main branch, never promotes a scaffold, and never rewrites a guardrail
  on its own. Use when the user says "sweep the repo", "check for memory drift",
  "what's gone stale", "entropy report", "run the nightly audit", or invokes
  /atra-sweep, and as the body of any scheduled memory-maintenance job.
---

The memory layer rots as the code moves. A sweep measures the rot and proposes
repairs — but disposing of them stays a human (or at least a gated) act, because
in code a confidently-wrong "fix" to a guardrail is worse than the drift it
replaces. **Propose, never commit.** That single rule is what makes it safe to
run this unattended.

## The trust split

Not all entropy needs judgment. Sort every check into the cheapest tier that can
handle it, and only escalate what truly needs a model or a human.

| Tier | What it does | Risk | Cadence |
|---|---|---|---|
| **lint** | mechanical drift via grep + git (no LLM) | none — read-only, deterministic | every commit + nightly |
| **judgment** | the calls only a model can make (is this rationale stale?), drafts fixes | low — writes to a report + branch only | nightly |
| **human** | approves the branch / answers DECISIONs | — | on review |

The bundled `scripts/atra_lint.py` is the whole lint tier. Run it first; it does
the cheap work and tells the judgment pass where to look.

## What counts as entropy (and what doesn't)

Staleness is measured in **development, not calendar time.** The unit is commits
in a plan's *neighborhood* (its directory / linked subsystem) since it was
written — the "has the trunk grown past the branch point?" signal — not days. A
plan three months old in a dormant repo is fine; one bypassed by 30 commits of
nearby work is suspect. (Tokens and sessions are a truer unit still, but they
live in the agent runtime, not git; commits are the best proxy git exposes.)

Two independent axes, easy to conflate: the sweep's *run cadence* (when you
check — nightly, per-PR, on demand) is wall-clock and arbitrary; the staleness
*metric* (how you decide a plan diverged — development past its branch point) is
not. You can check the tree any day you like; the moment it actually diverged is
fixed by where the growth went, not by when you looked.

Detected drift:

- **dead link** — a `related:`-context `[[X]]` whose target no longer exists.
- **register mismatch** — a heavy node inline with no register row, or a register
  row whose inline node was deleted.
- **aging node** — a SCAFFOLD / EXPERIMENT whose neighborhood took more than
  `--age-commits` (default 25) while the node itself didn't move.
- **passed gate** — a SCAFFOLD/EXPERIMENT whose `gate:` names a test that now
  exists / passes → candidate for promotion.
- **fulfilled future** — a `future: [[X]]` whose target now exists. The future
  arrived but the label still says "future" → promote `future:` → `related:`.
  Mechanical and high-confidence (the one case where a forward-link has ground
  truth: it shipped).
- **aging future** — a `future: [[X]]` unbuilt while its neighborhood moved past
  it by more than `--future-age-commits` (default 40, deliberately high). A gentle
  "still the plan?" — not a defect. Long-horizon planning is the point; a plan in
  a *still* neighborhood is never flagged, because no growth means no signal.
- **expired guardrail** — a `do-not ... until [[Mxx]]` whose milestone is marked
  done.
- **stale rationale** *(judgment)* — a `why:` whose surrounding code changed after
  the annotation was last touched. Heuristic; always a human-review flag, never an
  auto-edit.
- **abandoned future** *(judgment only)* — a plan silently dropped while its anchor
  code stays alive. Even neighborhood-growth can't prove this (code can re-attach
  late, unlike a tree); it needs a human, or an `unless:` condition that has
  provably fired.
- **unanswered DECISION** — a DECISION bypassed by more than `--decision-commits`
  (default 20) of work piling on top of the unmade decision — the dangerous case.
- **over-density** — a file or a single function carrying more *assistive*
  annotation than its budget: more than `--max-nodes-per-function` (default 1)
  nodes on one function, or assistive node-lines exceeding the
  `--node-line-ratio` (default 25 code-lines per node-line, with a
  `--density-floor` of 1 free node-line and the ratio applied only once a file
  has ≥ N code lines). The finding names the deterministic *lowest-value* node to
  promote to the store. Pointers count; guardrails never do.
- **should-externalize** — a *heavy* inline assistive block (≥ `--heavy-node-lines`,
  default 4) whose neighborhood has grown past `--externalize-threshold`
  (default 40 commits, deliberately high). The rationale earned its inline slot
  when the region was small; now it taxes every passer-by → move the payload to
  `docs/atramentous/store/<slug>.md` and leave a `[[store:<slug>]]` pointer.
  Small / young / dormant regions are never flagged.
- **consult-gateless** — a `CONSULT` node (a decision deferred to a human) whose
  `gate:` names no `[[phase]]`. A deferred consultation without a gate to a named
  phase is the "later means never" failure — it decides by neglect. Structural and
  deterministic (presence of a `[[link]]` in the gate, not its resolution: a gate
  to an unbuilt milestone is correct). Guardrail-exempt. See *Working with a human
  collaborator* in the grammar.

**Guardrails are exempt from both density findings.** A node whose status is
`SAFETY` or `SPINE`, or that carries a `do-not:` field, is a guardrail: it is
never budget-counted, never externalized, never suppressed. The density and
growth tiers govern *assistive* memory only — safety memory stays inline and
always-visible regardless of how dense or how grown the region is. A dead
`[[store:<slug>]]` pointer (no note at that slug) surfaces as an ordinary
`unresolved-link`.

Every magnitude above is a CLI flag whose default is a **reasoned default — tune
with use, not empirically derived**, never a hardcoded conviction (see
`atra_lint.py --help`).

**Never flagged as drift** (the line between entropy and the roadmap):

- **forward-links in a still neighborhood.** A `future: [[GPU Brush Engine]]` whose
  area hasn't grown is *correct* — unresolved is its normal state, and nothing has
  grown past it. Forward-links are exempt from *dead-link* detection, and exempt
  from *staleness* until development actually moves past them. Unresolved ≠ stale;
  bypassed-by-growth is stale.
- **old-but-true memory.** Calendar age is not staleness. A five-milestone-old
  `why:` that still matches the code stays. Only contradiction-with-reality, or
  growth past a plan, is drift.

## Procedure

1. **Lint.** Run `scripts/atra_lint.py --json --since-last`. It emits structured
   findings and an entropy count, and (with `--since-last`) the delta vs the last
   recorded sweep for the trend line.
2. **Judge the flags the linter couldn't.** For each stale-rationale heuristic and
   each ambiguous gate, decide whether it's real. Do not promote anything — just
   classify: real-drift / false-positive / needs-human.
3. **Draft, don't commit.** Stage the *safe* repairs (repoint a dead link, close a
   register orphan, demote an expired guardrail to a plain note) onto a branch
   named `atra/sweep-<date>`. Leave the *consequential* ones (promote a scaffold,
   rewrite a guardrail, delete REMOVABLE code) as **proposals in the digest**, not
   commits — those are `atra-reconcile`'s job under human eyes.
4. **Write the digest** to `docs/atramentous/sweeps/<date>.md` and update
   `docs/atramentous/sweeps/latest.md`. Record the entropy count so the next sweep
   can compute the trend.
5. **Open the gate.** In CI, open a PR from the branch (the PR is the human gate).
   Locally, leave the branch and print the digest path. Never merge.

## Digest format

Skimmable, severity-grouped, trend on the first line:

```
Atramentous sweep — 2026-06-28
entropy: 14 (3 high, 6 med, 5 low)   trend: ↑2 since 2026-06-21

HIGH
- dead link  BrushPipeline.kt:40  [[ADR-0008 Pressure Model]] → target missing
- gate met?  DebugRenderer SCAFFOLD  gate [[TEST RendererParity]] now passes → propose promote
- orphan     register [[Legacy Tile Path]] → no inline node

MED  …
LOW  …

proposed on atra/sweep-2026-06-28 (safe, awaiting your merge):
  · repoint 1 dead link   · close 1 register orphan   · demote 1 expired guardrail

needs you:
  · DECISION [[ADR-0011 Undo Granularity]] open 12 days
  · promote? DebugRenderer (gate passed) — run atra-reconcile to dispose
```

The `trend` line is the point. Findings trending down = the discipline is
winning. Trending up across several sweeps = memory debt is outrunning
maintenance; surface that to the user directly.

## In-session use

Invoked by hand (not on a timer), run the lint tier and report the digest inline.
Scope to the area the user is touching when they're mid-task — surface the open
scaffolds, unanswered DECISIONs, and guardrails for *that* area, not the whole
repo. Budget it: a few high-signal lines, then stop. Surfacing is a courtesy, not
a wall of audit output.

## Boundaries

- **Proposes, never commits to main.** No autonomous promotion, no guardrail
  rewrite, no deletion of live code. The branch/PR/digest is the whole output.
- **Read-mostly.** The only writes are the digest, the sweep-history record, and a
  clearly-named proposal branch. Nothing else.
- **Trust the code over the note.** When memory and code disagree, the finding is
  "the note is suspect," never "change the code to match the note."
- **Don't run untrusted gates blindly.** Executing a test named in a `gate:` is
  opt-in (`--run-gates`); by default the sweep *surfaces* the gate for a human to
  run, it doesn't execute arbitrary code from an annotation.
- Disposition is `atra-reconcile` (human-driven). Sweep finds and proposes;
  reconcile, with a person, promotes and deletes.
