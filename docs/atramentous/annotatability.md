# This repository's annotatability

Atramentous dogfoods its own annotatability rule (see "Annotatability" in
`atramentous/references/grammar.md`). This repo carries no machine register, so the
per-file determination is recorded here as the cached judgment — decided once,
inherited thereafter, not re-inferred per visit.

| files | annotate | why |
|---|---|---|
| every `SKILL.md` (`atramentous/`, `atra-sweep/`, `atra-review/`, `atra-reconcile/`, `atra-rehydrate/`, `atra-weave/`, `atra-map/`) | **external-only** | A skill's `SKILL.md` is a **product artifact** — it *is* the deliverable Cowork loads. An Atramentous block inside it would corrupt the shipped thing, so notes about a skill must live in the store with a relocated pointer, not inline. This is the forcing case: Atramentous could not dogfood itself until it could declare these external-only. |
| design / research docs (`README.md`, `FUTURE.md`, `ATRA-ANNOTATABILITY.md`, `atramentous/references/*.md`, `atra-sweep/harness/README.md`, this file) | **inline** | These exist *to hold* memory and rationale — a note linking a decision back to code is legitimate marginalia here, not noise. Same `.md` extension as a `SKILL.md`, opposite determination: annotatability is a judgment about whether a note belongs, not an extension lookup. |
| source (`atra-sweep/scripts/atra_lint.py`, harness scripts) | **inline** | Ordinary code with comment syntax; notes belong at the code site. |

None of the `external-only` files above currently carries a guardrail, so there is
nothing to relocate and the linter reports no `guardrail-needs-relocation` for this
repo. Were a guardrail ever needed *about* a `SKILL.md` (or another external-only
file), it would have to reach rung 2 — a `[[store:<slug>]]` summons on an
annotatable neighbor on the access path — never degrade to pointer-less.
