# Grammar provenance — why `invariant:` and `enforced-by:` exist

Short, durable note so these fields aren't unexplained later. Both came from M1, the
first real Atramentous experiment (2026-06). See M1-EXPERIMENT-RECORD.md for the full
arc.

## `invariant:` field  (+ linter finding `do-not-needs-invariant`)

WHY IT EXISTS: In M1, an inline SPINE guardrail on `activePath()` carried a `do-not`
that ENUMERATED forbidden fields — "sort by orderHint or created_at" — but did not list
`index`. A weak model (Haiku 4.5, no extended thinking) sorted by `index`, walking
straight through the gap the enumeration left, and broke the invariant the guardrail
existed to protect. The pretask code's own fallback also index-sorted, reading as
license.

THE LESSON: a `do-not` that lists instances has gaps a literal reader exploits. Stating
the *general invariant* (the principle of which the forbidden actions are instances)
closes them, and the discipline of writing the invariant line forces the author to
generalize — which surfaces omitted instances like `index`.

THE FIX: `invariant:` field, required for SPINE/SAFETY, recommended wherever a `do-not`
appears. Linter finding `do-not-needs-invariant` (STRUCTURAL — fires on field
presence/absence only; it does NOT and must NOT judge whether the invariant is
well-stated, which no deterministic check can do). The grammar carries the quality fix;
the linter only flags the missing field. Committed; the docs' own example blocks were
updated to model the rule they teach (dogfooding).

## `enforced-by:` field

WHY IT EXISTS: M1 also showed that even a clearly-worded inline guardrail is just prose
the model can choose to read past — and a weak model did. Prose informs; it does not
bind.

THE LESSON: the strongest guardrails are not better-worded comments but comments paired
with a *test that fails when the invariant is violated* — something in the execution
path the agent trips over, not text it can skip.

THE FIX: `enforced-by:` field points a critical guardrail at the test that mechanically
catches its violation (e.g. `enforced-by: [[test:active-path-branch-purity]]`).
RECOMMENDED for critical guardrails, not required (not every guardrail has or needs a
test). An unresolved `[[test:...]]` is a forward-reference (like `future:`), NOT a
high-severity broken pointer — the test may not exist yet. An optional
`guardrail-unenforced` finding was left to implementer judgment, with a strong lean
against adding it if it would be noisy (i.e. if most guardrails legitimately lack
tests). Verify the as-built status against the repo.

## The meta-point (worth keeping)

Both fields were discovered by a FAILED experiment, not by review. A careful human
reading that guardrail would have generalized "don't sort by timestamps" to "don't sort
by index" automatically and never noticed the gap. It took a literal-minded weak model
walking through the gap to expose that `do-not` fields have an enumeration-vs-invariant
failure mode. Contact with reality found what reasoning could not — which is the whole
premise of running the experiments at all.
