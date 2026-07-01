---
name: atra-review
description: >
  Reviews a diff or a set of files for MISSING project memory — irrecoverable
  rationale, absent semantic links, undocumented scaffolds, unstated lifecycle
  gates, missing safety guardrails — and emits one finding per line. Where a
  typical code review hunts what to delete or fix, this one hunts what a future
  agent will wish had been recorded. Use when the user says "review for missing
  memory", "what will future me forget here", "did I leave enough context",
  "audit the annotations", or invokes /atra-review. Lists findings; does
  not write the memory itself.
---

Review for memory that will be lost, not code that should be cut. The best
outcome is a fresh agent being able to resume this code without asking anyone.

For each file or hunk, apply the litmus test on the author's behalf:

> If this agent's context were wiped, what would the next one regret not finding
> here?

Then emit findings. One line each.

## Format

`<file>:L<line>: <tag> <what's missing>. <what to record>.`

Tags:

- `why:` a non-obvious decision with no recorded rationale. Name the decision.
- `link:` work that touches a known system / test / ADR / milestone with no
  `[[link]]` to it. Name the target.
- `forward:` code that assumes future work with no `future:` link reserving it.
- `gate:` a SCAFFOLD or EXPERIMENT with no testable promotion/kill condition.
- `safety:` a destructive / data-loss / validation path with no SAFETY node or
  `do-not` guardrail.
- `register:` a heavy node (scaffold/experiment/decision) absent from the register.
- `cluster:` a semantic cluster — a conceptual group with non-local edit
  consequences — is missing a link. Flag only when a future agent could
  plausibly edit one member in isolation and damage the others in a way the
  build system won't catch — not because files are thematically similar or
  share a folder.
- `research:` code depends on math/UX/design/research rationale that is not
  linked. Flag only when a future agent would plausibly "simplify" the code into
  a generic version because the bespoke reasoning isn't recorded — not merely
  because the code lacks an explanatory comment.
- `stale:` existing memory that now contradicts the code (a link to a deleted
  system, a gate that already passed, a "do not until M12" past M12).

## Examples

❌ "You might want to consider adding some documentation about why the renderer
abstraction exists, since it could be unclear to future readers."

✅ `RendererAbstraction.kt:L1: why: three backends planned, none stated. Record: exists to host CPU + Vulkan + future GPU behind one seam.`

✅ `BrushPipeline.kt:L40: link: depends on pressure model, no link. Add [[ADR-0008 Pressure Model]].`

✅ `TileCache.kt:L12: forward: assumes GPU residency that doesn't exist. Reserve [[GPU Tile Residency]].`

✅ `ExperimentalBrush.kt:L8: gate: EXPERIMENT with no kill condition. Record what test promotes or retires it.`

✅ `SavePipeline.kt:L55: safety: atomic-swap path, no SAFETY node. Record the temp→verify→swap invariant and do-not-replace-in-place guardrail.`

✅ `DebugRenderer.kt:L3: stale: gate "after M14 parity" — M14 shipped. Promote to REMOVABLE or delete.`

✅ `TargetMagnetism.kt:L18: cluster: tunes aim magnetism alongside input smoothing and reticle easing with no link between the three; a solo edit here can make the feel model inconsistent. Add [[Aim-Assist Feel Model]] related: across the three files, stating the non-local risk.`

✅ `CameraEase.kt:L22: research: bezier easing curve matches the UX perceptual-overshoot study, no link. Add related: [[research/camera-motion-ux.md]] and an invariant preserving the overshoot bound so a future agent doesn't "simplify" it to a stock ease.`

## Scoring

End with the count that matters: `gaps: <N> (why <a>, link <b>, gate <c>, safety <d>, cluster <e>, research <f>, stale <g>).`

If nothing is missing, say `Memory intact. A fresh agent can resume this.` and stop.

## Boundaries

- Scope: missing or stale **memory** only. Correctness bugs, security holes,
  performance, and over-engineering are out of scope — route those to a normal
  code review.
- Apply the budget in reverse too: do **not** flag recoverable facts as missing.
  If the code already says it, its absence as a comment is correct, not a gap.
  Flagging recoverable facts manufactures the noise the discipline exists to
  prevent.
- Don't flag `cluster:` or `research:` on vague "these are related" vibes. Only
  flag when a future agent would plausibly edit one file in isolation and damage
  the whole, or would replace a bespoke choice with a generic one because the
  rationale is absent. Thematic similarity alone is not a finding.
- Lists findings; does not write them. Hand the list to the persistent mode or
  to atra-weave to fill.
