---
name: atra-rehydrate
description: >
  Cold-start procedure for picking up an unfamiliar or resumed repository:
  reconstruct intent, constraints, in-flight work, and hidden dependencies from
  the memory layer — markers, links, the register, and maps — BEFORE editing any
  code. The consumer side of Atramentous (the inverse of leaving memory). Use
  when the user says "pick up where we left off", "rehydrate", "I'm resuming this
  project", "get up to speed on this repo", "what was I doing here", "context got
  wiped", or invokes /atra-rehydrate, and at the start of any session on a
  codebase you did not just write.
---

You are arriving with an empty context window. Before you touch code, read the
memory the previous agent left. Editing first and discovering intent later is how
agents undo their own past work.

## Procedure

1. **Read the index, not the tree.** Open the register
   (`docs/atramentous/register.md` or the project's scaffolding register) and any
   `docs/atramentous/` maps first. This is the table of contents for intent.
2. **Sweep the markers.**
   - `grep -rn ATRAMENTOUS` → every heavy node (spine, scaffold, decision, safety).
   - `grep -rn 'atra:'` → every breadcrumb.
   - `grep -rn 'DECISION'` → anything awaiting human/product review. Surface these
     to the user; do not resolve them silently.
   - `grep -rn 'SCAFFOLD\|EXPERIMENT'` → what's intentionally incomplete and why.
3. **Walk, don't read everything.** Pick the area you're about to touch. Follow
   its `related:` and `future:` links outward one or two hops. The graph tells you
   what this code depends on and what depends on it — far faster than reading the
   whole subsystem.
4. **Recover the three things agents forget**, per area:
   - **Why** does this exist the way it does? (look for `why:` and SPINE nodes)
   - **What must I not do?** (look for `do-not:`, SAFETY, "do not until Mxx")
   - **What's mid-flight?** (look for SCAFFOLD gates not yet met)
5. **Check for stale memory before trusting it.** A gate that already passed, a
   link to a deleted file, a "future" that shipped — note these; they're
   reconcile work, and they mean the memory is partly out of date. Trust the code
   over a contradicting note, and flag the contradiction.
6. **State your reconstruction back to the user** in a few lines before editing:
   what this area is, why it's shaped this way, the active scaffolds/gates, the
   guardrails, and any DECISION nodes that need them. Then proceed.

## Output shape

```
Resuming <area>.
  intent:   <why it exists, from the memory layer>
  in-flight: <open scaffolds + their gates>
  guardrails: <do-not / safety nodes that bound my edits>
  decisions: <DECISION nodes needing your input, if any>
  stale:    <memory that contradicts the code, if any>
Proceeding unless you redirect.
```

## Boundaries

- Read-only reconstruction. Rehydrate does not edit code or memory; it loads
  context and reports. Fixing stale memory is `atra-reconcile`.
- Don't re-derive what the memory already states. The point is to *use* the
  recorded intent, not to re-reason it from scratch — that's the context you were
  meant to save.
- If the repo has little or no memory layer, say so plainly and fall back to
  ordinary code reading. Absence of memory is itself a finding worth reporting.
- Surface DECISION nodes to the user rather than choosing for them. A decision
  deferred for human review stays deferred until a human weighs in.
