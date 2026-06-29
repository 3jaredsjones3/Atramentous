# Atramentous Grammar (canonical reference)

The full specification for the annotation system. Each skill restates the
minimal subset it needs so it works when installed alone; this file is the
source of truth when the whole collection is present.

## Two forms

**Breadcrumb** — the common case. One inline line. Most memory is this.

```
// atra: [[A]] → [[B]]  <=1 clause of why
```

**Heavy block** — reserved for SPINE, SCAFFOLD, EXPERIMENT, DECISION, SAFETY.

```
// ATRAMENTOUS  <STATUS>
// why:    ...
// related: [[...]] [[...]]
// future:  [[...]]
// gate:    [[TEST ...]] / measurable condition
// risk:    ...
// do-not:  ...
```

Comment syntax follows the host language (`//`, `#`, `--`, `<!-- -->`). The
sentinel token `ATRAMENTOUS` (block) and prefix `atra:` (breadcrumb) are constant
across languages so a single grep finds every node.

## The sentinel

`ATRAMENTOUS` is the index key, not the meaning. `grep -rn ATRAMENTOUS` lists
every heavy node; `grep -rn 'atra:'` lists every breadcrumb; `grep -rn '\[\[' `
lists every link. Grep finds the node; the node carries the meaning in prose.

## Status (lifecycle markers)

The marker after the sentinel is the node's lifecycle status. These are the same
markers an AGENTS.md-style project already uses — Atramentous wraps them, it does
not replace them.

| status | meaning | advances to |
|---|---|---|
| `SPINE` (`PERMANENT-SPINE`) | central architecture; do not bypass | — (stable) |
| `SCAFFOLD` | temporary; expected to be replaced | PRODUCTION / REMOVABLE |
| `EXPERIMENT` | testing a hypothesis | PRODUCTION / REFERENCE / removed |
| `REFERENCE` | non-production correctness oracle / comparison target | DEPRECATED |
| `PRODUCTION` | current intended implementation | DEPRECATED |
| `DEPRECATED` | present but receives no new features | REMOVABLE |
| `REMOVABLE` | all replacement gates passed; delete when safe | (deleted) |

Companion single-purpose markers that may appear as status or as a `do-not`/`risk`
qualifier: `SAFETY`, `PERF`, `DECISION`, `TODO`, `FIXME`.

| status | meaning | advances to |
|---|---|---|
| `CONSULT` | a decision deferred to a human at a *named future phase* — a consultation scaffolded for when it becomes ripe to judge | resolved (record a `DECISION`) / dropped |

`CONSULT` is a scaffold aimed at a person rather than at code (see *Working with a
human collaborator*). Like any forward-looking node it is only honest with a
gate: its `gate:` **must** name the phase where it becomes decidable. A `CONSULT`
with no `[[named phase]]` gate is the "later means never" failure and the linter
flags it (`consult-gateless`).

## Fields

| field | meaning | required for |
|---|---|---|
| `why:` | rationale the code cannot express | almost all blocks |
| `related:` | `[[...]]` links to existing systems / tests / ADRs / milestones | breadcrumb, block |
| `future:` | `[[...]]` links to **unwritten** code + intended action. Promote to `related:` when fulfilled; remove when the plan dies. | SCAFFOLD |
| `unless:` | optional, for load-bearing forward-links: the condition that abandons the plan (makes a dropped future provably dead) | forward-links a scaffold depends on |
| `gate:` / `promote-when:` | testable condition that advances the lifecycle | SCAFFOLD, EXPERIMENT |
| `risk:` | what breaks if forgotten or retained too long | SCAFFOLD, DECISION |
| `do-not:` | guardrail a future agent might trip | SPINE, SAFETY |
| `default:` | the provisional decision in effect *now*, so a deferred consultation never blocks | CONSULT |
| `ask:` | the single judgment/feel/intent question to put to the human when the gate's phase arrives | CONSULT |

### Required-field contract by node type

- SPINE → `why` + `do-not`
- SCAFFOLD → `why` + `future` + `gate` + `risk`
- EXPERIMENT → `why` + `gate`
- DECISION → `why` + rejected alternatives + `risk`
- SAFETY → `why` + `do-not` + the invariant that must hold
- CONSULT → `why` (what makes it not agent-decidable) + `default` (provisional answer in effect) + `gate` (the `[[named phase]]` where it ripens) + `ask` (the one question)
- Breadcrumb → links (+ optional one-clause why)

## Links

Obsidian-style `[[Stable Name]]`. Conventions:

- Milestones: `[[M14 Vulkan Renderer]]`
- ADRs / decisions: `[[ADR-0003 Renderer Abstraction]]`
- Tests: `[[TEST RendererParityTests]]`
- Spine systems: `[[SPINE Command Bus]]`
- Safety paths: `[[SAFETY Atomic Save]]`
- Scaffolds: `[[SCAFFOLD DebugBitmapCanvasRenderer]]`

Forward-links to unwritten code are first-class: `[[GPU Brush Engine]]` may not
exist yet. That's the point — the link reserves the connection so the future
work arrives pre-wired into the graph.

But forward-links are exempt from *dead-link* detection, **not** from staleness.
The roadmap rots too: a plan gets fulfilled, renamed, superseded, or abandoned.
A `future:` link therefore has a lifecycle — promote it to `related:` once the
target ships, and remove it if the plan dies. Measure that staleness in
*development, not calendar time*: a plan is stale when work has grown past the
point it needed to attach, not when N days passed. Three drift cases, by how much
ground truth exists:

- **fulfilled** (mechanical) — target now resolves → promote `future:` → `related:`.
- **aging** (heuristic) — the plan's neighborhood moved past it by many commits
  while it stayed a stub → "still the plan?". A still neighborhood is never
  flagged: no growth, no signal.
- **abandoned** (judgment) — silently dropped; only a fired `unless:` makes it
  provable (code can re-attach late, so growth-past is a prompt, not a verdict).
  Unresolved ≠ immune.

## The register

Canonical index of heavy nodes. Default `docs/atramentous/register.md`; a project
with an existing `docs/scaffolding_register.md` should reuse it. One row per heavy
node:

```
| ID | status | location | introduced | gate | risk |
```

Inline annotations are distributed memory; the register is the index over them.
`atra-reconcile` keeps them in sync; `atra-map` reads from both.

## The externalized tier (the store)

Inline memory is the fast tier: greppable, always-visible, read by every agent
that passes the code. But heavy rationale read by *few* agents *rarely* taxes
*every* agent that scrolls past it. As a region matures, that imbalance grows.
The store is the slow tier — a relief valve that keeps the inline layer thin
without losing the rationale.

**Layout.** Heavy assistive rationale lives one-note-per-file at
`docs/atramentous/store/<slug>.md`. The `<slug>` is lowercase kebab-case, stable,
unique — and it *is* the note's ID. The code keeps only a breadcrumb pointer to
the note; the payload moves out.

**Note format.** YAML frontmatter + body:

```
---
id: renderer-parity-rationale      # == the slug; the note's identity
title: Why the CPU path is the parity oracle
status: SCAFFOLD                   # the lifecycle status of the node it carries
links: [[M14 Vulkan Renderer]] [[TEST RendererParityTests]]
register: SCAFFOLD DebugBitmapCanvasRenderer   # optional back-ref to register row
---

why: ...the full rationale that used to sit inline...
related: [[...]]
future: [[...]]
risk: ...
```

**Pointer syntax** (the breadcrumb left behind in the code):

```
// atra: see [[store:<slug>]] — <the concrete failure that follows from not querying it here>
```

- The `store:` namespace inside the link marks an externalization pointer.
  `grep -rn 'store:'` lists every pointer; `[[store:<slug>]]` resolves iff
  `docs/atramentous/store/<slug>.md` exists (a pointer to a missing note is a
  dead link like any other).
- The trailing clause is mandatory and must state the *failure averted* by
  knowing to look there — not "more detail in the store." A pointer earns its
  slot only if not knowing to query the note would cause a concrete mistake.

**What may be externalized — assistive memory only.** Externalization is a tool
for `why:` / `related:` / `future:` / `risk:` weight. It is governed by the same
density and growth rules that govern any assistive node.

**What never leaves the code — guardrails.** A node is a **guardrail**, defined
mechanically, if its status is `SAFETY` or `SPINE`, **or** it carries a `do-not:`
field. Guardrails stay inline and always-visible regardless of density or
growth. Never move a guardrail's payload to the store, never replace it with a
pointer, never count it against a density budget. Safety memory must be in front
of the agent at the moment it could trip the wire — a pointer there is a latency
the wire can't afford.

**Pointers count against the budget.** A pointer is a node. A wall of
"maybe check the store" summons is exactly the noise the budget exists to kill,
so pointers are budgeted like any other node (see below). Externalizing heavy
rationale and then leaving five pointers to it has not reduced density.

## The memory budget (anti-noise law)

Memory is read by every future agent, so it pays rent or it isn't written:

1. Never annotate what the code already says.
2. One fact, one home — link, don't copy.
3. Prefer a link to a paragraph.
4. Record reason, not implementation.
5. Fails the litmus test ("would a fresh agent regret its absence?") → it's
   prose, delete it.
6. When a region's inline memory outgrows its budget, **move heavy assistive
   rationale to the store and leave a pointer** — don't delete the rationale, and
   don't leave it inline taxing every passer-by. Guardrails are exempt: they stay
   inline always (see the externalized tier above). Density is enforced by
   `atra-sweep` (`over-density`, `should-externalize`).

## Working with a human collaborator

The mechanics above decide *what memory to keep*. This decides *when to interrupt
a person* — the other half of collaboration. Every decision the agent meets during
work resolves on two axes:

1. **Can I decide this well?** (is it within agent judgment, or genuinely
   subjective / intent-bound / risk-bound in a way only the human can settle?)
2. **Must it be decided well *now*?** — or is there a later point that is both
   *cheaper to change* and *easier to judge* (something real to look at)?

Four quadrants:

| | must decide now | can wait |
|---|---|---|
| **decidable** | decide it; record a `DECISION` node; proceed | decide provisionally; `SCAFFOLD` it with a gate; proceed — bother no one |
| **not decidable** | **escalate** (four-part format below) | **scaffold the consultation**: leave a `CONSULT` gated to the phase where it ripens; proceed silently |

The fourth quadrant is the one most agents get wrong — they either ask now (too
early to judge) or never (silent decision by neglect). Do neither. **Confirming a
decision later is just future scaffolding aimed at a person**: leave a gated
`CONSULT` node and proceed. When that phase arrives, the sweep surfaces it and the
human is asked — batched, against something real, at peak decidability.

Example: during a get-it-usable phase, exact UI panel widths are subjective (the
agent can't judge them by feel) but cheap to change and *better judged later
against a running interface*. The agent does not ask now and does not ask after —
it leaves a gated `CONSULT` and proceeds:

```
// ATRAMENTOUS  CONSULT
// why:     panel widths are a feel-call; can't be judged by eye pre-render
// default: 280px side / 1fr main — provisional, in effect now so nothing blocks
// gate:    [[M12 UI Polish]] — batch a human feel-test here
// ask:     do these proportions feel right against the running interface?
```

At `[[M12 UI Polish]]` the sweep surfaces it and a batch of such feel-calls go to
the human together, at peak decidability.

### Escalation format (must-decide-now + not-decidable only)

A halt-and-wait escalation is allowed **only** when it carries, in this order:

1. **What happened** — one line.
2. **What I already determined** — the forensics, done by the agent and never
   handed up as a chore: reconstruct from git history, the surrounding code, the
   `do-not` clause. The human inherits conclusions, not homework.
3. **What I'll do by default** — a concrete recommended action, not "how should I
   proceed?".
4. **The one question** — phrased so the answer is a judgment / risk / intent
   call, never a fact the agent could have established itself.

Test of a well-formed escalation: *could the agent have answered its own question
by working harder?* If yes, it is not ready to escalate — that's risk-offloading,
not consultation. Reserve escalation for genuine subjectivity the agent can't
resolve. A bare "go fix this" alert with no four parts attached is never allowed.

### Reversibility prior (this collaborator's stated preference)

> This human prefers a wrong default they can correct over a question they can't
> yet answer. Bias hard toward **act-and-report** for anything cheap to reverse.

"Reversible" means cheap to reverse *including everything later built on it*. Git
makes the mechanical undo free, but a foundation that twenty dependent tasks now
assume is **not** cheap to reverse. So confirm load-bearing-but-early decisions at
a *near* checkpoint — a few milestones out, not twenty — via a scaffolded
`CONSULT`: early enough that the blast radius is still small, late enough that
there is something real to judge.

### Invariants

- A deferred `CONSULT` **must** carry a `gate:` to a **named phase**
  (`[[Mxx ...]]`), never "later". A consultation without a gate is "later means
  never" wearing politeness — it decides by neglect. This is the forward-link
  honesty rule applied to decisions, and the linter enforces it
  (`consult-gateless`).
- **Don't escalate to offload risk.** If the agent could decide better than most
  users, it decides, records a `DECISION`, and proceeds — surfacing for review
  without blocking. Escalation is for what the agent genuinely cannot judge.
- **Halt-and-wait requires the four-part escalation.** No bare alerts.

## Never embed

Secrets, tokens, credentials, or personal data. Memory is durable and committed;
it lives forever in version control.
