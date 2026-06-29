# Atramentous — FUTURE.md (design memory, not yet built)

<!-- ATRAMENTOUS  REFERENCE
why: this file is the project's own memory of decisions reasoned-through but not
     yet built. It exists because the alternative is that the why evaporates and a
     future agent (or the author) re-derives it from scratch — the exact disease
     Atramentous treats. Dogfooding: the project keeps its own intent the way it
     asks its users to.
related: [[grammar.md]] [[atramentous/SKILL.md]]
do-not: treat anything here as committed behavior. These are reasoned bets and
        deferred work, not shipped features. Build order and triggers are stated
        per item; respect the triggers (don't build deferred items ahead of the
        evidence that justifies them).
-->

This records what was decided but not built, why, and what would trigger building
it. Three piles, kept separate on purpose: **forced-now**, **phase-two
(evidence-gated)**, and **the measurement that validates the whole thing**.

---

## 0. The thesis, stated so it can be wrong

The bet under Atramentous, in one line: **the dominant failure mode of agent
coding is missing context at the point of decision, not insufficient capability.**
A smarter agent reasoning over an incomplete picture still reaches a confidently
wrong conclusion. The fix is therefore not a smarter agent but a *present* one —
the load-bearing intent in the file the agent opened, single-hop, un-missable.

Sharper form: **informational alignment, not value alignment.** Most agent
failures are the agent not *knowing* the governing fact, not the agent *wanting*
the wrong thing. "Aligned information is all you need" — cheeky, deliberately
reductive, almost certainly incomplete, but possibly right about *where the
substrate is*. Like "attention is all you need," its value is not completeness;
it is naming the axis a whole solution-space can organize around. Atramentous is
**one inhabitant** of that space (bets: in-code, in-git, inline-first,
guardrail-asymmetric), not the space itself. claude-mem is another inhabitant with
opposite bets. The frame survives any single inhabitant failing.

Deeper reframing (held, not yet load-bearing in the build): intent is not a thing
*stored at the start and delivered downstream* — it is a property of the parts
**cohering as the system grows**, generated during development in response to
challenges the prompt never anticipated (cf. an organism: no cell holds the
blueprint; "be human" was never a spec any part received). Under this view
Atramentous is less a *memory* and more a **coherence-maintenance layer**:
staleness detection, forward-link fulfillment, reconcile, and forgetting are all
operations that keep a continuously-regenerated intent consistent with the tree.
The final judge is **consistency tested against contact with the world** — internal
coherence alone is underdetermined (a tumor is locally consistent and fatal). This
is why the battery (§3) is not optional: it is the contact that judges whether the
coherence is the viable kind.

---

## 1. Forced-now — annotatability & graceful degradation

**Full spec:** see `ATRA-ANNOTATABILITY.md` (this session's output). Summary here so
the why survives even if that file doesn't travel with the repo.

**Problem.** The core mechanism assumes "annotate in place," but annotatability is
a property of the *file*, not universal. CSV/strict-JSON have no comment syntax;
generated files lose notes on regen; product artifacts (incl. **`SKILL.md` — which
is why Atramentous cannot currently dogfood itself**) have syntax but a note
corrupts the artifact. Two `.md` files can have opposite annotatability (research
doc: notes belong; SKILL.md: they don't) — so it's a **judgment**, decided once and
cached in the register, never re-inferred per visit.

**Resolution — the greedy degradation ladder.** Take the highest reachable rung:
1. **inline** — note at the code site (full locality).
2. **externalize + relocated pointer** — payload to the store; the L0 pointer moves
   to the **nearest annotatable neighbor on the access path** (the loader that
   imports the CSV, not an arbitrary sibling — greedy on proximity-in-access-flow,
   not in-filesystem; this is the one place naive greed underperforms).
3. **externalize, pointer-less** — recorded in the store, no summons (the
   consultation-rate weak spot).
4. **lost** — only if no annotatable surface is reachable anywhere; still a register
   row, so never truly zero.

Never cliffs to nothing while any surface is reachable → **better than vanilla for
every file**, the spatial form of "better than vanilla at every lifecycle point."

**Guardrail invariant (hard).** A `do-not:`/`SAFETY`/`SPINE` note about an
`external-only` file MUST get a relocated pointer (rung 2); it may not degrade to
pointer-less. If no neighbor exists on the access path → **escalate** (four-part
format), never silently accept. A guardrail with no summons is a protection that
silently stopped protecting. Assistive notes may degrade to rung 3.

**Build scope.** NOW: the `external-only` register value; the rule that
product-artifact files (incl. SKILL.md) get it; guardrail relocation +
escalate-if-no-neighbor. DEFER: the full annotatability-inference engine and
access-path resolver, until a CSV/generated-heavy repo exercises them.

---

## 2. Phase-two — cross-store curation (evidence-gated)

Trigger: **only once a real claude-mem-style transcript store is accumulating real
noise on a long-running project.** Until there is a swamp, the editor has nothing
to edit. Do not build ahead of this.

**Idea.** Atramentous (the *why*) becomes the **editorial / relevance authority**
over a claude-mem-style transcript store (the noisy *what*). The hardest problem in
auto-capture memory is the **forget decision**, and a transcript can't make it well
from inside its own data — relevance requires *intent*, which is exactly what the
transcript lacks and Atramentous holds. A cluster of "what we did to X" observations
stays relevant while X's intent node is live; when that node goes
`DEPRECATED`/`REMOVABLE`, the cluster is safe to forget — grounded in *meaning*, not
age. Reuse the `should-externalize`/staleness signal as the forget-oracle.

**Bidirectional (the more valuable direction).** The transcript's
*persistent-but-un-annotated* patterns flag **gaps in Atramentous** — load-bearing
activity with no recorded why. Surface them as candidate intents for a human to
promote. So: Atramentous edits the transcript *down*; the transcript feeds
Atramentous *up*. A loop, not a parallel pair.

**Why it's safe (the realization that dissolved the main risk).** Atramentous lives
**in git, versioned with the code**. Forgetting is therefore a **visibility**
operation, not destruction — a pruned note is in history, recoverable by `git log`.
This converts the one irreversible-looking failure (wrong forget) into something
reversible, putting it on the act-and-report side of the reversibility prior. Bonus:
git supplies the *evolution-of-what* for free (commit history) and, because the why
is in the same repo, the *evolution-of-why* on the same substrate — one timeline,
one checkout, both layers move together. This retroactively justifies the
daemon-free flat-markdown bet: temporal recoverability was a free rider on
"files-in-git, not a database-beside-code."

**Discipline (hard).** Propose-never-delete, same as the sweep. Guardrail-linked
observations are never auto-forgotten even if they look stale. Human disposes. Do
**not** let the pruning pass become an auto-deleter, just as the store must not
become an auto-capturer — keep the authored/captured line bright, or you've rebuilt
claude-mem worse and without its infrastructure. The value is judgment-grade
forgetting, which is exactly what the intent layer can supply and the transcript
can't.

---

## 3. The measurement — the landmine battery (built, not yet run)

**Status:** harness built (`atra-battery/`, this session's output), deliberately
not run. Reasoning suffices for *derivable* improvements; the battery is reserved
for the genuinely undecidable question.

**The undecidable question it exists to answer:** *do agents actually follow a
`[[store:<slug>]]` pointer when they should?* The entire externalization
architecture — every rung-2/3 degradation, the whole store — rests on this, and it
is NOT reasoning-decidable; it depends on real model behavior. First battery job: a
landmine whose guardrail lives behind a pointer vs inline — does avoidance survive
the indirection? A clean answer validates or **kills** the store design.

**Pre-registered (see `atra-battery/PREREGISTRATION.md`):** H1 memory>stripped; H2
(the wrongable one) weak models benefit *more*. Engaged-gate = the fast-but-wrong
guard. Tripwires committed before running.

**The two-tailed honesty:** an unrun prediction is two-tailed. It could come back
*better* than projected (weak-model gains larger than simulated; one prevented
compounding catastrophe worth more than the per-case sum; the consultation model
producing a qualitative "agent stopped interrupting me" shift the battery can't even
score) as easily as worse. The frame becomes a *research program* rather than
philosophy exactly when an inhabitant of it beats vanilla measurably. This is that
measurement.

---

## 4. Minor / non-blocking

- `atra-weave`, `atra-review` are store-blind. Defensible (neither needs the store
  for its core job). Decide: close (weave→link code to store notes; review→flag
  store notes with no inbound pointer) or mark deliberate. Not urgent.
- On-disk `collection/*.zip` go stale; run `scripts/build-collection.sh` before any
  distribution. (Correctly git-untracked.)
- Parked micro-opts, evidence-gated: `weak:` pointer flag + harness strip (only if
  pointer-line input tokens prove significant at scale); token-cost-visibility in
  the sweep digest; session/token counter as a truer staleness unit than commits
  (only if the commit proxy proves misleading).

---

## Method note (the rule that governed all of the above)

Test when you can't reason to the answer; reason when you can; don't mistake a
guessed magnitude for a derived one. Directions are derivable (locality raises
consultation reliability; externalization trades locality for capacity; forgetting
needs an intent-oracle). Magnitudes are assumptions held as tunable parameters, not
convictions. The battery is spent only on a fork reasoning genuinely cannot
settle — of which "do agents follow pointers" is the first real instance.
