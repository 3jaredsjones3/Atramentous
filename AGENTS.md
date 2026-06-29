# AGENTS.md — house rules for working ON Atramentous

Read this before editing this repo. It is the standing operating contract for any
agent (Cowork, Claude Code, or otherwise) doing work here. A task handoff should
NOT need to restate these — they live here so the task can be just the task.

This is dogfooding: Atramentous's own operating intent, embedded in Atramentous,
delivered single-hop to the next agent. If this file works, it is itself a small
proof of the thesis — embedded intent survived the handoff.

---

## Orient first (rehydrate-for-this-repo)

The memory layer for THIS project lives in:
- `README.md` — what Atramentous is and the skill map.
- `atramentous/SKILL.md` + `atramentous/references/grammar.md` — the canonical
  grammar. **grammar.md is the source of truth for built behavior.**
- `FUTURE.md` — design reasoned-through but NOT yet built (forced-now /
  evidence-gated / the measurement). Don't treat it as shipped behavior.
- `ATRA-ANNOTATABILITY.md` and other `ATRA-*.md` — standalone design specs.

The seven skills: `atramentous` (persistent mode) + `atra-weave`, `atra-review`,
`atra-rehydrate`, `atra-reconcile`, `atra-map`, `atra-sweep`.

## The canonical linter (one home, beware the stale mount)

- The ONLY linter is `atra-sweep/scripts/atra_lint.py`. There is no other copy.
  If you find a second `atra_lint.py` anywhere, it is stale debris — do not edit
  it, delete it.
- **The Linux bash mount has repeatedly served a STALE, truncated copy of this
  file.** Verify against git / the real tree (Windows shell, Desktop Commander)
  before trusting a read or a self-test. State which source you used.

## The self-test is the gate

- After EVERY change: `cd atra-sweep/scripts && python3 atra_lint.py --selftest`
  must exit 0. Green before you advance a stage; green before you commit.
- **Additive only.** Never alter or weaken an existing finding kind or assertion.
  New behavior gets new assertions. If you must touch existing logic, say so
  explicitly and update the docstring/README.
- Findings are structural / deterministic. **No LLM judge, no fuzzy heuristic**
  where a mechanical check works.
- **Derived-not-stored.** No finding writes a persistent log/state file; the sweep
  recomputes from the live tree every run.

## Invariants you must not redefine

- **Guardrail predicate (reuse verbatim):** a node is a guardrail iff its status is
  `SAFETY`/`SPINE` OR it carries a `do-not:` field. Guardrails are never
  budget-counted, never externalized, never auto-deleted, never suppressed. Every
  new rule that touches guardrails reuses `nd["guard"]` — do not invent a new
  guardrail definition.
- **`external-only` vs `local-only` are different axes.** `external-only` =
  the FILE can't/mustn't hold notes. `local-only` = a NODE is site-bound. Don't
  conflate them.
- **`CONSULT` stays out of `OPEN_STATUSES`** (don't perturb the aging logic).
- **Product artifacts carry no inline ATRAMENTOUS blocks.** `SKILL.md` files are
  the product; a note inside one is a bug. They are `external-only`. (This is why
  the annotatability tier exists — see `ATRA-ANNOTATABILITY.md`.)

## Escalation & human consultation (when you hit a real fork)

The four-quadrant rule (full text in grammar.md "Working with a human
collaborator"): decide-and-record-a-DECISION when you can decide well and it must
be decided now; **scaffold a gated CONSULT** when it's not-decidable-now but ripens
at a named phase; escalate (four-part: what happened / what you determined / your
default action / the one judgment question) only when it's not-decidable AND
must-be-now. Bias to act-and-report for anything cheap to reverse — this maintainer
prefers a wrong default they can correct over a question they can't yet answer. A
deferred consultation MUST carry a gate to a named `[[Mxx]]` phase, or it's the
"later means never" failure.

## Reporting back

Report the **instrument, not just that tests pass**: the predicates you added
(verbatim), the behavior text, the parameter defaults, and the specific test cases
that prove a safety-sensitive rule. The maintainer reviews the design, not only the
green check — especially anything touching guardrails.

## Mechanics

- Commits are currently **unsigned** (no GPG key on the build machine) — expected,
  not an error.
- `collection/*.zip` are build artifacts, git-untracked; regenerate with
  `scripts/build-collection.sh` before distributing. Never commit them.
- Parameters are tunable flags with **reasoned, non-empirical defaults** —
  documented as "tune with use, not measured." Don't harden a default into a
  conviction.

## The one rule under all the rules

When unsure whether something belongs inline, in the store, or nowhere: leave what
a fresh agent would need to resume after its context is gone, and nothing more.
Better than vanilla at every point in the lifecycle is the bar — never make a file
or a moment worse than it would be with no memory at all.
