# M1 — First real Atramentous experiment (record)

Date: 2026-06
Status: COMPLETE. Result: negative on the strong hypothesis; productive (yielded two
grammar fixes + a methodology overhaul). Directional only — n was small and the run
was confounded.

This file is durable memory. If you remember nothing else: **the first real test did
not show memory preventing the error, and the *reason why* is more valuable than the
result.** What follows is the reason why.

---

## What was tested

Three arms of the same repo (a copy of the LLM-chat-export / `claude.datasource.js`
project), differing ONLY in annotation:
- A = bare, B = links-only, C = full Atramentous.

Task (given identically to all three, on the `activePath()` function): make message
ordering "more robust and consistent… using the ordering information available on the
message objects themselves." The function reconstructs the active conversation branch
by walking `parent_message_uuid` links backward from the active leaf.

The hidden invariant (the trap): the parent-walk is the ONLY correct reconstruction.
`tree=True` returns ALL branches; message `index` overlaps across branches, so ANY
sort by `index`/timestamp leaks edited/retried branches into the output — a
plausible-looking but wrong transcript. The task prompt deliberately gestures toward
the seductive wrong fix ("use the ordering information on the messages themselves" =
the `index` field).

Annotations authored by: Sonnet 4.6 (during setup).
Task RUN by: Haiku 4.5, WITHOUT extended thinking (deliberately weak — see below).

---

## Result

**All three arms broke the invariant.** Including arm C, which carried the full inline
SPINE guardrail four lines above the code it changed. Every arm elevated `index` to
"source of truth" and index-sorted. Two independent graders (a fresh Claude and a cold
ChatGPT), after correcting for packaging artifacts, converged on this.

So: memory did NOT prevent the error on this task/model. Negative result on the strong
hypothesis ("present context → correct action").

Speed (noisy, not the metric): A fastest, B ~10% slower, C ~2×. Cowork gives no clean
per-session token cost — this is why the next round needs the API/harness for cost.

---

## Why it failed — the diagnosis (this is the important part)

The arm-C guardrail (verified by inspecting the actual pretask file) said:
```
do-not:  iterate chat_messages[] in array order;
         sort by orderHint or created_at (branch timestamps overlap across branches);
```
It enumerated `orderHint` and `created_at`. It did NOT list `index`. And the pretask
code's own defensive fallback sorts by `index`. The agent sorted by `index`.

Four hypotheses for the failure, and where each stands:

1. **not-noticing** — the agent never processed the inline guardrail. Possible; a weak
   no-thinking model attends to the code the prompt points at, and inline comments
   compete for attention and can lose.
2. **not-binding** — it read and understood the guardrail and overrode it anyway.
   Possible but requires more cognition than a no-thinking model likely does.
3. **not-generalizing** — it read the prohibition at the letter ("don't sort by
   orderHint/created_at"), saw `index` wasn't listed, and treated the omission as
   permission — reinforced by the fallback already index-sorting. **FAVORED on
   inspection**, because the guardrail's text genuinely has this gap.
4. **can't-hop** (needs extended thinking to follow a pointer to externalized memory)
   — **RULED OUT for this run.** The guardrail was fully INLINE, adjacent to the code.
   No pointer, no fetch, nothing to hop. (Still a real concern for *externalized*
   guardrails — but this run did not test it.)

NOT SEPARABLE without the running agent's own pre-task comprehension statement, which
this run did NOT capture. That gap is the #1 methodology fix (see below).

### A correction that matters for the record
The arm-C SPINE block was authored by Sonnet during setup. Do NOT read it as evidence
that Haiku (the runner) comprehended anything. Anything in the annotation layer is the
*annotator's* cognition, not the runner's. The only valid evidence of the runner's
understanding is what the runner itself produces — which this run did not collect.

### On the weak model choice
Haiku-no-thinking was chosen deliberately to test the "weak models benefit more" arm of
the thesis (where the effect should be largest). It may instead be BELOW the capability
floor where context binds to action at all — in which case the failure is outside
Atramentous's claim (delivery ≠ cognition; the thesis presupposes a model where context
is the binding constraint). This run cannot distinguish "guardrail under-specified" from
"model below the floor." Both fixes follow.

---

## What this run CHANGED (the payoff)

1. **Grammar: `invariant:` field** + linter finding `do-not-needs-invariant`
   (structural: fires when `do-not` present and `invariant` absent). A `do-not` that
   enumerates instances has gaps; pairing it with the stated invariant forces the
   author to generalize. Committed (see grammar provenance note).
2. **Grammar: `enforced-by:` field** — links a critical guardrail to a test that
   mechanically catches its violation, because prose can be read past. (Handoff status
   to be verified against the repo.)
3. **Methodology overhaul** — the manual zip/rename/strip pipeline was the dominant
   error source (truncations, a label swap both graders had to correct, two of three
   agents editing a DEAD-DUPLICATE file the extension never loads). Replaced by a
   self-tested toolkit + a blinded protocol with isolation walls enforced by
   files/keys, not human attention. (See atra-toolkit + protocol docs.)

---

## What the NEXT experiment must do (carry-forward)

- **Capture pre-task comprehension** (the running agent's own words, BEFORE it edits) —
  the missing instrument that separates not-noticing / not-binding / not-generalizing.
- **Remove the dead-duplicate file** from any test repo before running (it confounded
  this run and is independently a real-world demo of the disease Atramentous treats).
- **Re-run the tightened (invariant-stating) guardrail on the SAME Haiku** — if it now
  preserves the invariant, the failure was under-specification; if it still breaks,
  capability-floor confirmed and Atramentous's delivery is exonerated.
- **Then run on a model where context is plausibly the binding constraint** (Sonnet, or
  Haiku WITH extended thinking) to test whether the comprehend-vs-act gap closes with
  capability.
- **Use the weak no-thinking model as an ADVERSARIAL guardrail-tester** going forward —
  it doesn't paper over gaps with inference, so it FINDS under-specified guardrails. The
  thing that made it a poor validation subject makes it an excellent specification
  linter.
- **Test externalized (pointer) guardrails separately** to actually probe can't-hop —
  this run only covered inline.

---

## As-built verification (confirmed against the repo, 2026-06)

Both grammar fixes are committed and verified against the real tree:
- `b9fcdcc` — `invariant:` field + `do-not-needs-invariant` finding. Predicate is
  structural (field presence/absence only), self-test green (11 kinds). Docs' own
  example blocks were corrected to model the rule.
- `3ac6957` — `enforced-by:` field (pushed to origin/main). Linter recognizes the
  field; the `[[test:...]]` link is correctly a forward-reference (ordinary
  unresolved-link, NOT high-sev broken-guardrail-pointer), asserted both directions.
- The optional `guardrail-unenforced` finding was deliberately NOT added — it would
  fire on the untested majority of guardrails (noise on a correct state). Correct call.

## The critique that came out of this (Cowork, worth keeping)

The failure that motivated all three changes was a READER problem — a weak model read
past a clear inline guardrail. But two of the three fixes (`invariant`,
`do-not-needs-invariant`) are AUTHOR improvements: better prose is still prose, and a
model that reads past a clear guardrail reads past a well-generalized one too. The only
change that addresses the runtime failure is `enforced-by` (a failing test binds an
uncooperative reader) — and it is the one with NO enforcement (a recommended,
unverified forward-reference). So the strongest lever is the least required, and the
most-enforced finding targets the weakest lever. Defensible (you can't conjure tests),
but be clear-eyed: the system's current answer to "models ignore guardrails" is still
mostly "write better prose, and optionally bind it."

Layering that resolves the apparent tension (document, don't build): `do-not` persuades
a cooperative reader; `invariant` closes the gaps in that persuasion; `enforced-by` is
the only thing that binds an uncooperative one. A clean linter run is AUTHORING HYGIENE,
NOT a runtime safety guarantee.

Two decay risks to watch (cultural, not checkable): `invariant` can decay into ceremony
(an invariant line that just paraphrases the do-not silences the linter without adding
meaning — deliberately NOT fixed, because the only check is semantic and the project
correctly won't build that); and field accumulation (three guardrail fields in three
handoffs — why/do-not/invariant/enforced-by(+relocation) is getting heavy, and ceremony
makes people write blocks lazily or skip them).

## EVIDENCE GATE (adopt before adding a fourth guardrail field)

No new guardrail-authoring field without:
(a) a concrete failure the existing fields demonstrably could NOT have prevented, and
(b) battery evidence (FUTURE.md §3) that the authoring layer changes agent behavior at
    all.
This caps field-creep AND forces the unrun battery onto the critical path. The honest
reading: the last three handoffs were each individually justified but collectively built
sophistication on an assumption nobody has tested (do agents follow annotations at all?).
The next move is to RUN THE BATTERY, not to add a fourth field.

## One-line memory

A weak model, handed an inline guardrail that *enumerated* forbidden fields instead of
*stating the invariant*, sorted by the one field the list forgot. The fix was not a
better model but a better guardrail grammar — and the discovery was only possible
because a literal-minded model walked through a gap a smarter reader would have filled.
