# Atramentous — Annotatability & Graceful Degradation (rev. 2)

Status: design spec, ready to fold into `grammar.md` and a Cowork handoff.
Supersedes rev. 1. Changes: the ladder is reframed as **forced, not chosen**
(greedy local optimization under per-file constraints); the relocated guardrail
pointer is reframed as **coherence maintenance**, not just fact delivery.

The core mechanism assumes "annotate in place." That assumption is false for a
large class of files. This spec formalizes the fallback: a per-file
**annotatability** determination and a **greedy degradation ladder** that always
takes the best memory a file can support, never falling to nothing while any
reachable annotatable surface exists.

---

## The gap

"In place" is only available when the place accepts annotation. It does not, for:

- **No comment syntax** — CSV, TSV, strict JSON. Cannot hold a note at all.
- **Generated / vendored files** — a note is lost on regeneration.
- **Product artifacts** — the file *is* the deliverable, so a note corrupts its
  meaning. A `SKILL.md` has comment syntax but an Atramentous block inside it is
  itself a bug, because the skill is the product. (Atramentous's own repo is full
  of these — its dogfooding forcing function: it cannot annotate its own skills
  until this exists.)

Annotatability is therefore a **property of the file, not of its syntax**. Two
`.md` files can have opposite annotatability: a research/design doc welcomes a note
linking it back to code; a `SKILL.md` does not. The distinction is *does a note
belong here* (legitimate marginalia vs noise in the artifact), which is a
**judgment**, not an extension lookup.

## The determination (decided once, cached — not re-inferred per visit)

Each file gets an annotatability value, recorded in the register the first time an
agent needs to annotate it (or proactively at rehydrate):

| value | meaning |
|---|---|
| `annotate: inline` | comments belong; normal Atramentous applies (the default) |
| `annotate: external-only` | file cannot or must-not hold notes (no syntax / generated / product artifact); memory goes to the store |

The mechanical part (has comment syntax? generated?) is cheap. The **judgment**
part (is a comment *appropriate* here — `SKILL.md` vs research doc) is why this is
**recorded once, inherited thereafter**, not re-derived every visit. Re-litigating
a settled judgment on each touch is exactly the waste Atramentous exists to remove:
the first agent to reason "product artifact → no inline notes" writes
`annotate: external-only`; every later agent inherits the call. This is the litmus
test applied to the annotatability decision itself.

## The greedy degradation ladder

**This is not a designed feature set — it is a forced move.** A file that cannot
hold text about itself offers no "keep inline locality" option; the only choice the
file leaves is *how much* of the ideal you can recover, and the answer is "the best
reachable rung." That is precisely greedy local optimization: when constraints vary
per file and there is no global structure to exploit, taking the locally-best
available option at each file *is* the correct algorithm, not a compromise. The
ladder is Atramentous's existing per-case greed (inline vs breadcrumb vs block vs
externalize) continued past the point where the obvious move runs out.

Take the highest reachable rung:

1. **Inline** — file is `inline`: note at the code site. (Full locality: L0
   pointer/clause is in the file the agent opened. Best case.)
2. **Externalize + relocated pointer** — file is `external-only` but a good
   annotatable neighbor exists: payload -> `store/<slug>.md`; the **L0 pointer moves
   to the nearest annotatable neighbor on the access path**, pointing inward at the
   silent file. (Locality preserved through one hop.)
3. **Externalize, pointer-less** — `external-only` and no annotatable neighbor on
   the path: note recorded in the store with no summons. (The consultation-rate
   weak spot — assistive only; see guardrail rule.)
4. **Lost** — only if no annotatable surface is reachable *anywhere* near the file.
   Effectively unreachable; even here it is a register row, so never truly zero.

**Graceful degradation by construction.** Each step down is small; the rule never
cliffs to "nothing" while any annotatable surface is reachable. So it is **better
than vanilla for every file** — even the worst case leaves a recorded store note,
strictly more than the zero a vanilla agent leaves. This is the *spatial* form of
"better than vanilla at every point in the lifecycle": better for every *file*, not
just every *moment*. A greedy rule that always grabs the best-available option is
guaranteed never-worse-than-baseline anywhere, and usually better.

## The one place naive greed underperforms — the access-path rule

Greedy algorithms fail exactly when a local win forecloses a global one. Here:
dropping the note on the *filesystem-nearest* neighbor is a local win (a slot was
found) that can be a global loss (the summons isn't on the path an agent actually
takes to reach the silent file).

**Rule:** rung 2's "nearest annotatable neighbor" means **nearest on the access
path**, not nearest in the directory — the loader that imports the CSV, the module
that reads the generated file: the doorway an agent passes through to reach the
silent file. Still greedy; greedy on the *right* metric (proximity-in-access-flow,
not proximity-in-filesystem). This is the only spot where naive nearest-neighbor
quietly underperforms, and it is cheap to get right.

## Guardrail rule — coherence maintenance, not just delivery

A silent guardrail is the worst case in the whole system. The relocated pointer is
not merely "deliver the fact elsewhere" — it is **keeping the silent file and its
governing constraint coherent as the structure grows.** The CSV and the invariant
that governs it must stay *connected*; the relocated pointer is the edge that holds
that connection when the file itself cannot. Losing the edge doesn't just lose a
fact, it lets two parts of the system that depend on each other drift apart
silently — the exact incoherence Atramentous exists to prevent.

Therefore:

- A `do-not:` / `SAFETY` / `SPINE` note about an `external-only` file **MUST** get a
  relocated pointer (rung 2). It may **not** degrade to rung 3 (pointer-less). If no
  annotatable neighbor exists on the access path, that is an **escalation** (four-
  part format), not a silent acceptance — a guardrail with no summons anywhere is a
  protection that silently stopped protecting.
- An *assistive* note may degrade to rung 3 if no good neighbor exists. Losing
  assistive reach costs convenience; losing guardrail reach costs a hazard. Same
  asymmetry that governs everything else in the system.

## Why this is forced, not chosen (the honest framing)

There is no menu. A file that cannot hold text about itself offers no "keep inline
locality" option — the alternative to externalizing is *no memory there at all*. The
ladder recovers as much as each file physically permits. `external-only` files are a
genuinely **weaker tier** (the relocated pointer is a hop away, not in place, so the
guarantee degrades from "can't miss it" to "very likely on the path") — and that
weakness is the ceiling the file imposes, not a design compromise. The system is not
settling; it is doing the best each file allows, which is what greedy local
optimization *is*. The absence of a choice is the system working as designed: it
takes the best each file can give, and the worst it ever does is still better than
the blank slate.

## Build scope (greedy here too — forced-now vs deferred)

- **Now** (Atramentous's own repo forces it — `SKILL.md` files can't hold notes, so
  it can't dogfood itself without this): the `annotate: external-only` value; the
  rule that product-artifact files (incl. `SKILL.md`) get it; the guardrail
  neighbor-relocation + escalate-if-no-neighbor; mark this repo's own SKILL.md files
  external-only as the dogfooding proof.
- **Defer** (until a CSV/generated-file-heavy real repo exercises them): the full
  annotatability-inference engine and the access-path neighbor resolver. Reasoned
  defaults, parameterized, not built ahead of a repo that needs them.

## Relationship to `local-only` (don't conflate)

`external-only` is about the **file's capacity** to hold notes. `local-only` is
about a **node being site-bound** (meaningless away from its exact code location).
Different axes: a node can be `local-only` in an `inline` file (kept inline, never
externalized) or live in an `external-only` file (externalized because the file
can't hold it). The linter treats them as independent conditions.
