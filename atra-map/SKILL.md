---
name: atra-map
description: >
  Generates navigable maps of a repository from its Atramentous annotations and
  register — subsystem maps, milestone maps, decision maps, safety maps,
  scaffolding maps, and a link atlas — so a large project stays traversable by
  meaning instead of by grep alone. Semantic, not syntactic (the meaning-level
  counterpart to a call graph). Use when the user says "map the repo", "show the
  architecture", "atlas", "what scaffolds are open", "decision log", "milestone
  map", or invokes /atra-map. Produces map documents; reads the memory
  layer, does not modify code.
---

Turn the accumulated memory layer into something a person or agent can read
top-down. The annotations already encode the graph; this skill renders views of
it. Most useful once a repo is large enough that grep-and-read stops scaling.

## Procedure

1. **Collect the graph.** `grep -rn ATRAMENTOUS` + `grep -rn 'atra:'` +
   `grep -rn '\[\['` and parse the register. Nodes = annotated locations; edges =
   `related:` / `future:` links; attributes = status, why, gate, risk.
2. **Render the requested views** (default: all that have ≥1 node). Write to
   `docs/atramentous/maps/`. Each map is a markdown document, not a comment.

| Map | Shows | Built from |
|---|---|---|
| Subsystem map | files grouped by the systems they link to | `related:` clusters |
| Milestone map | what's done / in-flight / planned per `[[Mxx]]` | milestone links + scaffold gates |
| Decision map | every DECISION node, its rationale, rejected alternatives, status | DECISION nodes |
| Safety map | every SAFETY path and its invariant + guardrails | SAFETY nodes |
| Scaffolding map | open scaffolds/experiments, their gates, their risk-if-retained | SCAFFOLD/EXPERIMENT + register |
| Link atlas | the raw node→node graph (incl. forward-links to unwritten code) | all links |

3. **Mark the frontier.** Forward-links whose targets don't exist yet are the
   project's planned edge — list them explicitly as "reserved / unwritten" so the
   map shows where the work is heading, not just where it's been.
4. **Flag inconsistencies you pass** (dead links, gates that look passed,
   register mismatches) as a short appendix — but don't fix them. Fixing is
   `atra-reconcile`.

## Output shape

A small set of linked markdown maps under `docs/atramentous/maps/`, each opening
with a one-line legend, the node list with `[[links]]` intact so the maps are
themselves navigable, and a "frontier" section for unwritten targets. Render a
diagram (mermaid/dot) only when the graph is small enough to read; past a few
dozen nodes, a grouped list beats a hairball.

## Boundaries

- Read-only over code and inline memory. Writes map documents under
  `docs/atramentous/`; changes nothing else.
- Renders the graph that exists; does not invent edges. If two things should be
  linked but aren't, that's a finding for atra-review, not a line to draw.
- Don't let maps become a second source of truth. They're a rendered view —
  regenerate them from the annotations; never hand-edit a map and expect it to
  hold. The inline memory and the register are canonical; maps are derived.
