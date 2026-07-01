# Drop-in block for AGENTS.md — the guardrail-field evidence gate

Add this under the house rules. It came out of M1 (2026-06): three guardrail-authoring
fields were added in three handoffs, each individually justified, but collectively
building sophistication on an untested assumption (that agents follow annotations at
all). This rule caps the creep and forces the verification onto the critical path.

---

## Evidence gate for guardrail-authoring fields

Do NOT add a new guardrail-authoring field (a new `do-not`/`invariant`/`enforced-by`-
class field) without BOTH:

1. **A concrete failure the existing fields demonstrably could not have prevented.**
   Not a plausible anecdote — a real case where `why` + `do-not` + `invariant` +
   `enforced-by`, correctly used, would still have failed. If the existing fields
   would have covered it, the fix is to USE them, not to add a field.

2. **Battery evidence (FUTURE.md §3) that the authoring layer changes agent behavior
   at all.** The whole guardrail-authoring stack rests on the premise that embedding
   intent changes what an agent does. That premise is, as of M1, UNTESTED. Until the
   battery shows the authoring layer moves outcomes, every new authoring field is
   sophistication on an unverified foundation.

### Why this gate, stated plainly
The layering the fields form — `do-not` persuades a cooperative reader, `invariant`
closes the gaps in that persuasion, `enforced-by` binds an uncooperative one — is
coherent. But note the asymmetry M1 exposed: the only field that addresses the actual
runtime failure (a model reading past prose) is `enforced-by`, and it is the least
enforced (a recommended, unverified forward-reference). The author-side fields make the
prose better; better prose is still prose. So before adding a FOURTH field, the
question is not "would this field help an author write a clearer guardrail" — it is
"do we have evidence that clearer guardrails change what agents DO." That evidence is
the battery. Run it before extending the layer.

### Corollary (the layering is not a safety guarantee)
A clean linter run is AUTHORING HYGIENE, not a runtime safety guarantee. `do-not-needs-
invariant` checks that an author wrote a field; it cannot check the field is honored at
runtime. State this wherever a green linter might be mistaken for "the guardrails hold."
