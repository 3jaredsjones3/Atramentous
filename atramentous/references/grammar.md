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

### Required-field contract by node type

- SPINE → `why` + `do-not`
- SCAFFOLD → `why` + `future` + `gate` + `risk`
- EXPERIMENT → `why` + `gate`
- DECISION → `why` + rejected alternatives + `risk`
- SAFETY → `why` + `do-not` + the invariant that must hold
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

## The memory budget (anti-noise law)

Memory is read by every future agent, so it pays rent or it isn't written:

1. Never annotate what the code already says.
2. One fact, one home — link, don't copy.
3. Prefer a link to a paragraph.
4. Record reason, not implementation.
5. Fails the litmus test ("would a fresh agent regret its absence?") → it's
   prose, delete it.

## Never embed

Secrets, tokens, credentials, or personal data. Memory is durable and committed;
it lives forever in version control.
