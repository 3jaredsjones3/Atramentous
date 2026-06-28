---
name: atra-reconcile
description: >
  Garbage-collection and lifecycle maintenance for the project's memory layer —
  promote scaffolds whose gates have passed, retire experiments, prune dead
  links, merge duplicated rationale, refresh stale notes, and resync the register
  with reality. This is memory maintenance, NOT code refactoring. Use when the
  user says "reconcile the memory", "clean up the annotations", "the comments are
  stale", "did any scaffolds graduate", "sync the register", "garbage-collect the
  notes", or invokes /atra-reconcile — typically when finishing a branch
  or after a burst of development. Advances and prunes nodes; does not change
  program behavior.
---

The memory layer drifts from the code as the code moves. Reconcile pulls it back
into sync. This advances and removes *notes*, never program behavior — if a
change here alters what the code does, you've left the skill's scope.

## Procedure

1. **Inventory.** `grep -rn ATRAMENTOUS` and `grep -rn 'atra:'` for the live
   nodes; read the register. You're comparing recorded memory against current
   reality.
2. **Advance passed gates.** For each SCAFFOLD / EXPERIMENT, check its `gate:`
   against the tests. Gate met → advance the node along the lifecycle
   (`SCAFFOLD → PRODUCTION`, or `→ REMOVABLE` if a replacement now exists;
   `EXPERIMENT → PRODUCTION / REFERENCE / removed`). Never advance a node whose
   gate has not actually passed — run the tests, don't assume.
3. **Retire what graduated.** A scaffold whose replacement shipped becomes
   `DEPRECATED` then `REMOVABLE`; delete `REMOVABLE` code when nothing depends on
   it. Update or remove the now-stale comment in the same change — a stale node
   is worse than none.
4. **Prune dead links.** Any `[[link]]` whose target was deleted or renamed:
   repoint it or remove it. A forward-link to a "future" that shipped becomes a
   plain `related:` link.
5. **Merge duplicated rationale.** Same `why:` in multiple places → keep one
   canonical home, replace the rest with links to it. This is the one-fact-one-home
   rule applied after the fact.
6. **Refresh stale guardrails.** "Do not simplify until M12" past M12 → lift it or
   restate the real current constraint. A guardrail no one can trust gets ignored,
   including the true ones next to it.
7. **Resync the register.** Every heavy node present inline appears in the
   register and vice versa; statuses match; closed items are marked closed.

## Output

A short ledger of what moved:

```
promoted:  [[DebugBitmapRenderer]] SCAFFOLD → REMOVABLE (M14 parity green)
retired:   [[Legacy Tile Path]] DEPRECATED → deleted (no callers)
relinked:  BrushPipeline.kt [[Old Pressure]] → [[ADR-0008 Pressure Model]]
merged:    parity rationale ×3 → [[REFERENCE CPU Rasterizer]]
unblocked: TileCache.kt do-not lifted (M12 shipped)
register:  +2 rows synced, 1 closed
```

## Boundaries

- Memory only. Promoting a node may *enable* deleting dead code (a REMOVABLE
  path), and removing genuinely dead code is in scope; changing the behavior of
  *live* code is not — route that to a normal refactor.
- Don't advance on assumption. A gate is passed when its tests are green, not
  when it looks done. If you can't run the gate, leave the node and say so.
- Don't delete memory that still pays rent just because it's old. Age isn't
  staleness; contradiction-with-reality is. A five-milestone-old `why:` that's
  still true stays.
- Surface, don't resolve, DECISION nodes. Reconcile maintains; it doesn't make
  the human's call.
