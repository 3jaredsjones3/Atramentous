---
name: atra-weave
description: >
  One-shot pass that connects a piece of finished work into the repository's
  semantic graph — adds back-links to the existing systems, tests, ADRs, and
  milestones it touches, and forward-links to the unwritten code it will depend
  on or feed. Builds relationships, not comments. Use when the user says "weave
  this in", "connect this", "link this to the rest", "wire up the graph", "what
  does this relate to", or invokes /atra-weave after writing or moving
  code. Complements atramentous (the persistent mode); this is the focused
  graph-building operation.
---

Connect work into the semantic graph. You are not adding rationale here — that's
the persistent mode's job. You are adding **relationships** grep can't infer.

## Input

A unit of work: a new file, a moved module, a finished feature, a function the
user points at.

## Procedure

1. **Locate the node.** What is the smallest set of places where a link would
   actually be followed? Usually the file head and the one or two functions that
   are the real seams. Don't link every line.
2. **Back-links — what exists that this touches.** Grep the tree for the systems,
   tests, ADRs, and milestones it calls, extends, or depends on. Add `related:`
   links to each. Reuse existing `[[Stable Names]]` — search before you coin a
   new one.
3. **Forward-links — what's unwritten that this implies.** This is the part that
   pays off later. If the work assumes a future system, reserve the connection
   now with a `future:` `[[...]]` link even though the target doesn't exist. When
   that work arrives it lands pre-wired.
4. **Semantic clusters and research grounding — links mechanical tools can't find.**
   Ask two questions the import graph and call graph cannot answer:
   - Does this work belong to a **semantic cluster** — several files that implement
     one conceptual model with no import between them?
   - Is this work **grounded in research/design/math** reasoning that lives outside
     the code — a derivation, a UX study, a design decision?
   Do not write "link related files." That earns nothing. A cluster or grounding
   edge earns its place only when **editing one member in isolation would have a
   non-local consequence the build system can't see**, or when **research/math/UX/
   design rationale would otherwise be lost**. If neither is true, skip the link —
   thematic similarity alone is not a reason to connect two files.
   When it is true, add `related:` links across the cluster (or to the research
   artifact) and state the earned consequence — the non-local risk in `risk:`, or
   the preserved rationale in `why:`/`invariant:`. The stated consequence is what
   distinguishes a real cluster edge from decoration.
5. **Reciprocate where cheap.** If you link A→B and B is a node you can reach,
   add the B→A breadcrumb so the graph is navigable from both ends. Skip if B is
   large or unrelated-at-the-seam — don't spam.
6. **Register the heavy ones.** Any link that introduces or points at a SCAFFOLD,
   EXPERIMENT, or DECISION gets a register row.

## Form

Light by default:

```kotlin
// atra: [[Pressure Model]] [[M03 CPU Brush]] → [[GPU Brush Engine]] (unwritten)
```

Heavy only when the connection itself needs explaining:

```kotlin
// ATRAMENTOUS  REFERENCE
// why:     parity oracle for the future GPU path
// related: [[CPU Rasterizer]] [[TEST RendererParityTests]]
// future:  [[GPU Brush Engine]] must match this before [[CPU Rasterizer]] is removed
```

A semantic cluster or research-grounding edge is always heavy — it must carry the
consequence that earned it, not just the link:

```ts
// ATRAMENTOUS REFERENCE [[Aim-Assist Feel Model]]
// why:     input smoothing, target magnetism, and reticle easing implement ONE UX
//          feel model, even though they live in separate systems and don't import
//          each other.
// related: [[src/input/smoothing.ts]] [[src/combat/target-magnetism.ts]]
// related: [[src/ui/reticle-ease.ts]]
// risk:    tuning one file alone can improve a local metric while breaking the
//          whole feel model — reason about the cluster together, not singly.
```

## Naming

Coin a `[[Stable Name]]` only after grepping for an existing one. A new name for
an existing concept forks the graph. Names are durable — pick the one a future
agent would search for, not the one that's shortest to type.

## Boundaries

- Relationships only. If you're writing a paragraph of *why*, that's the
  persistent mode, not weave.
- Don't over-link. A node reachable five hops away through other nodes does not
  need a direct edge. The budget from `atramentous` applies: each link is read by
  every future agent.
- Forward-links to unwritten code are encouraged. Forward-links to code that
  *will never exist* are noise — only reserve connections the work actually
  implies.
- Don't map a semantic cluster that's just vibes. Files being thematically
  similar, touching the same feature, or living in the same folder is not
  enough — that is link-spam with extra steps. A cluster edge earns its place
  only when editing one member in isolation has a stated non-local consequence
  the build system can't see. No stated consequence, no edge.
- Does not refactor code. Adds edges to the graph and register rows; nothing else.
