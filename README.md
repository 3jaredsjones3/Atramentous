# Atramentous

> Clean code is easy to read. Atramentous code is easy to *resume*.

A skill collection that treats the source tree as a project's primary memory
store for future agents. It governs an axis most code discipline ignores: not
*how the code should be* or *how you should work*, but *how the next agent will
understand what you did* — durable rationale, semantic links between scripts
(including unwritten ones), and honest scaffolding embedded beside the code they
govern.

It exists because current agents lack persistent episodic memory. Rather than
fight that, Atramentous externalizes memory into the repository so every future
session starts from a self-explanatory codebase.

The central habit, asked before every meaningful change:

> **If my context window were wiped right now, what would I wish I had left
> behind in the repository?**

## The collection

| Skill | Type | Job |
|---|---|---|
| `atramentous` | persistent mode | The reflex, the grammar, the memory budget, scaffolding discipline. Self-sufficient alone. **Start here.** |
| `atra-weave` | one-shot | Connect finished work into the semantic graph — back-links and forward-links. |
| `atra-review` | one-shot | Audit for *missing* memory; emits findings, fixes nothing. |
| `atra-rehydrate` | one-shot | Reconstruct intent from the memory layer before editing an unfamiliar / resumed repo. |
| `atra-reconcile` | one-shot | Lifecycle GC: promote passed scaffolds, prune dead links, merge dupes, sync the register. |
| `atra-map` | one-shot | Render the navigable atlas from annotations + register. |
| `atra-sweep` | scheduled / on-demand | Autonomous entropy auditor. Proposes fixes onto a branch + writes a trend digest; never commits to main. Ships a deterministic linter + cron/CI harness. |

The persistent mode is the only one you typically enable by hand. The companions
match on demand or are invoked by name.

## The grammar in one screen

One greppable sentinel, a lifecycle status, a few typed fields, stable links.
This *wraps* an existing AGENTS.md-style marker vocabulary; it does not replace it.

Breadcrumb (the common case — one line):

```kotlin
// atra: [[M03 CPU Brush]] → [[M14 Vulkan Renderer]]  parity oracle, do not optimize
```

Heavy block (spine / scaffold / decision / safety only):

```kotlin
// ATRAMENTOUS  SCAFFOLD
// why:    CPU bitmap path makes tile output visible before the renderer exists
// related: [[M04 Android Canvas]] [[SPINE Tile Engine]]
// future:  [[M14 Vulkan Renderer]] replaces this
// gate:    [[TEST RendererParityTests]] green for every brush family
// risk:    diverges from the real renderer silently if retained past M14
// do-not:  add product-only behavior here
```

`grep -rn ATRAMENTOUS` finds every node. Grep locates the node; the node carries
the meaning. Full spec: `atramentous/references/grammar.md`.

## The one law that keeps it from becoming noise

Memory is read by **every future agent**, so it pays rent or it isn't written.
Never annotate what the code already says; one fact, one home (link, don't copy);
record reason, not implementation; if it fails the litmus test, it's prose —
delete it. Over-annotation is the failure mode, not under-annotation.

## Install

The unit of installation is **one skill folder**, zipped.

- **Cowork:** Customize → upload one zip per skill (in `dist/`). Matching is
  semantic; you won't name skills every time. Enable the mode with "use
  atramentous".
- **Codex:** drop each skill folder into the skills directory; it loads natively.
- **Claude Code:** place each folder in your skills directory (or
  `~/.agents/skills/`) and invoke via the `Skill` tool.

`dist/atramentous-collection.zip` bundles all seven for convenience; individual
`dist/<skill>.zip` files are the per-skill uploads. Details:
`atramentous/references/atra-tools.md`.

## Fits alongside other disciplines

Atramentous occupies its own axis and doesn't conflict with whatever governs how
your code is written or sequenced:

```
the code itself  → what is the right implementation?
the workflow     → what is the right sequence of steps?
Atramentous      → how will the next agent understand this?
```

If a discipline tells you to delete prose longer than the code, run the litmus
test as the tie-breaker: a comment that fails it is prose (delete it); one that
passes is memory (it stays, marked as a real node). Where memory work attaches to
a development cycle: record decisions when they're made, breadcrumb while
implementing, run `atra-review` before claiming done, run
`atra-reconcile` before wrapping up, and run `atra-rehydrate` when
picking a repo back up.

## Fighting entropy on a timer

Memory drifts from code as code moves; a stale note is worse than no note, because
an agent trusts it. `atra-sweep` keeps the drift bounded. It runs the cheap
deterministic linter (`atra-sweep/scripts/atra_lint.py` — grep + git, no LLM,
runnable on every commit) plus an optional nightly judgment pass, and emits a
trend digest so you can *see* whether memory debt is growing or shrinking.

The rule that makes unattended runs safe for code: **propose, never commit to
main.** The sweep writes a digest and stages safe repairs on a branch; promoting a
scaffold, rewriting a guardrail, or deleting live code stays with `atra-reconcile`
under a human. In CI the PR is the gate. Harness options (GitHub Actions, cron,
launchd, Cowork schedule) are in `atra-sweep/harness/`.

## Optional

A tiny `atra-help` reference-card skill is easy to add if you want
`/atra-help` to print the grammar without loading the mode.
Left out here to keep the set crisp; `references/grammar.md` already serves as the
reference.
