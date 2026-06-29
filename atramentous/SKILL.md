---
name: atramentous
description: >
  Persistent mode that treats the source tree as the project's primary memory
  store for future agents. Embeds durable rationale, semantic links between
  scripts (including to unwritten ones), and honest scaffolding directly beside
  the code it governs, so a fresh agent can reconstruct intent after its context
  window is gone. Use whenever the user says "atramentous", "leave breadcrumbs",
  "project memory", "annotate for future agents", "don't let me forget why",
  "obsidian-style links", "durable comments", or when working in a repo whose
  AGENTS.md / CLAUDE.md / GEMINI.md asks for agent-readable annotations,
  scaffolding markers, or a scaffolding/memory register. Stays active until
  turned off.
argument-hint: "[lite|full|ultra]"
license: MIT
---

# Atramentous

The source tree is the project's primary memory. Not the docs, not the tickets,
not the chat, not your context window — the code itself. You will forget why
this became what it is. Atramentous makes the repository remember for you.

Writing code is one axis; preserving *the memory about the code* is another —
the reasoning, constraints, and connections a fresh agent can't reconstruct from
the code alone. Atramentous governs the second axis. It sits beside whatever
discipline governs how the code itself gets written, without competing with it.

## The litmus test

Before every meaningful change, ask one question:

> **If my context window were wiped right now, what would I wish I had left
> behind in the repository?**

Record exactly that, where the next agent will naturally look, and nothing more.
Not "should I add a comment." The test is **regret**: would a fresh agent
*regret the absence* of this fact? If the code, types, and names already make it
recoverable, you add nothing. If the reasoning would be lost, you record it.

## Persistence

ACTIVE EVERY RESPONSE. No drift back to writing memory-less code, and no drift
into annotating everything. Still active if unsure. Off only: "stop atramentous"
/ "normal mode". Default: **full**. Switch: `/atramentous lite|full|ultra`.

## The memory budget (this is the spine)

Memory has a cost: **every future agent reads it.** Noise doesn't just fail to
help — it displaces signal and burns the next agent's context. So memory pays
rent or it doesn't get written.

1. **Never annotate what the code already says.** No `// increments i`, no
   restating the function name in prose. If grep + the type signature recover
   it, it is not memory, it is decoration. Delete it.
2. **One fact, one home.** State a rationale once, in its canonical place, and
   `[[link]]` to it from everywhere else. Five copies of the same "why" is five
   things to keep in sync and four things to go stale.
3. **Prefer a link to a paragraph.** A `[[ADR-0003 Renderer Abstraction]]` beats
   re-explaining the decision inline.
4. **Record reason, not implementation.** Agents forget *why*, not *what*. "This
   rasterizes brushes" is recoverable from the code. "This is intentionally
   slower because it is the parity oracle — do not optimize it" is not.
5. **If it fails the litmus test, it is prose, not memory.** Delete it. When a
   note is borderline, the test breaks the tie: regret its absence → memory;
   wouldn't → prose, cut it.

## The grep tension, resolved

Your links and markers *are* greppable — that's the point. `grep -rn ATRAMENTOUS`
finds every memory node; `grep -rn '\[\[Renderer'` finds every reference to a
system. What grep **cannot** do is infer the *relationships and rationale* a
node carries. Atramentous makes the meaning greppable-by-proxy: grep locates the
node, the node carries the meaning in natural language. Humans navigate by grep;
agents navigate by meaning. Leave both a handle.

## The grammar

One sentinel, one status, a few typed fields, stable links. This unifies with an
existing AGENTS.md marker vocabulary rather than competing with it: `ATRAMENTOUS`
is the index, the lifecycle marker is the node's status, the fields carry meaning.

### Lightweight breadcrumb (the common case — keep it to one line)

Most memory is a single inline line, not a block:

```kotlin
// atra: [[M03 CPU Brush]] → [[M14 Vulkan Renderer]]  parity oracle, do not optimize
```

`atra:` + the links it connects + at most a clause of why. If a clause won't
cover it, it earns a block. Most nodes never need a block.

### Heavy block (reserved for spine, scaffold, decision, safety)

```kotlin
// ATRAMENTOUS  SCAFFOLD
// why:    CPU bitmap path makes tile output visible before the renderer
//         abstraction exists. Lets us validate MotionEvent → Tile → screen now.
// related: [[M04 Android Canvas]] [[SPINE Tile Engine]]
// future:  [[M14 Vulkan Renderer]] replaces this
// gate:    [[TEST RendererParityTests]] green for every brush family
// risk:    if retained past M14 it diverges from the real renderer silently
// do-not:  add product-only behavior here; keep it a debug/reference path
```

Field set (include only fields that pass the litmus test — never all of them by reflex):

| field | meaning | used by |
|---|---|---|
| `status` | lifecycle marker after the sentinel: SPINE / SCAFFOLD / EXPERIMENT / REFERENCE / PRODUCTION / DEPRECATED / REMOVABLE | all heavy blocks |
| `why:` | the rationale the code can't express | almost always |
| `related:` | `[[...]]` links to existing systems / tests / ADRs / milestones | breadcrumb + block |
| `future:` | `[[...]]` links to **unwritten** code + what should happen there. Carries its own lifecycle: when the target ships, promote to `related:`; if the plan dies, remove it. | scaffold |
| `unless:` | (optional, for load-bearing forward-links) the condition under which the planned future is abandoned — makes a dropped plan provably dead instead of silently rotting | forward-links a scaffold depends on |
| `gate:` / `promote-when:` | the testable condition that advances the node's lifecycle | scaffold, experiment |
| `risk:` | what breaks if forgotten or kept too long | scaffold, decision |
| `do-not:` | the guardrail a future agent might trip | spine, safety |
| `default:` | the provisional answer in effect now, so a deferred consultation never blocks | consult |
| `ask:` | the one judgment/feel/intent question to put to the human when the gate's phase arrives | consult |
| `local-only:` | `true` = site-bound memory, never externalized to the store (a port of a `<private>` tag). A second exclusion from `should-externalize`; still budget-counted, and *not* a guardrail | any node whose rationale only makes sense in place |

### Required fields by node type

- **SPINE** (don't-bypass architecture): `why` + `do-not`.
- **SCAFFOLD** (temporary): `why` + `future` + `gate` + `risk`.
- **EXPERIMENT** (hypothesis): `why` + `gate` (what proves/kills it).
- **DECISION** (needs human review): `why` + the rejected alternatives + `risk`.
- **SAFETY** (data-loss / destructive / validation): `why` + `do-not` + the invariant that must hold.
- **CONSULT** (decision deferred to a human): `why` (what makes it not agent-decidable) + `default` (provisional answer in effect) + `gate` (the `[[named phase]]` where it ripens) + `ask` (the one question).
- **Breadcrumb** (navigation only): just `atra:` + links.

## Scaffolding is the reflex, not a chore

Outgrowing a seashell beats a tidy sequential workspace where you forget what you
were doing. When the real architecture doesn't exist yet, **do not pretend it
does and do not leave a bare `// TODO`.** Leave a structured `SCAFFOLD` block: why
the placeholder exists, what `[[future]]` thing replaces it, the `gate` that
promotes it, the `risk` if it lingers. A placeholder that links forward is a
node in the graph. A bare TODO is amnesia with a timestamp.

Lifecycle, always visible, never silent:

```
SCAFFOLD → EXPERIMENT → REFERENCE → PRODUCTION → DEPRECATED → REMOVABLE
```

Never silently convert a scaffold into production. Advancing a node is a
deliberate act with a passed gate (see `atra-reconcile`).

**The roadmap has a lifecycle too.** A `future:` link is a promise, and a promise
without a condition just sits and rots — a forward-link is a scaffold without a
gate. Plans get fulfilled, renamed, superseded, or abandoned, and a forward-link
that no longer reflects the plan misleads the next agent exactly like a stale
guardrail does. So forward-links are exempt from *dead-link* checks (being
unresolved is their normal state) but **not** from staleness: when the target
ships, promote `future:` → `related:`; when a plan dies, remove it. And measure
that staleness in *development, not time* — a plan is stale when work has grown
past the point it needed to attach (its neighborhood moved on without it), not
when a calendar threshold elapsed. For the few forward-links a scaffold's
promotion depends on, give them an `unless:` so abandonment is provable rather
than silent. Unresolved is not the same as immune; bypassed-by-growth is the
signal.

### Externalized tier (the store — for when inline memory grows heavy)

Inline memory is the fast tier: always in front of the next agent, but taxing
*every* agent that scrolls past it. Heavy rationale that few agents need, read
rarely, shouldn't tax everyone forever. As a region matures, move that weight to
a **store** and leave a thin pointer behind:

```kotlin
// atra: see [[store:renderer-parity-rationale]] — optimizing this path silently breaks brush parity
```

The payload lives one-note-per-file at `docs/atramentous/store/<slug>.md`
(YAML frontmatter `id`/`title`/`status`/`links`, then the heavy `why:`/`risk:`
body). The `<slug>` is the note's ID. `[[store:<slug>]]` resolves iff that file
exists, so a pointer to a missing note is a dead link.

Three things keep this honest, and they are not optional:

1. **Only assistive memory externalizes.** `why:` / `related:` / `future:` /
   `risk:` weight may move. The store is a tool for *density*, not for hiding.
2. **Guardrails never leave the code.** A node whose status is `SAFETY` or
   `SPINE`, or that carries a `do-not:`, is a guardrail — it stays inline and
   always-visible regardless of density or growth. A safety wire behind a pointer
   is a safety wire the agent trips before it reads. Never externalize one.
3. **Pointers count against the budget.** A pointer is a node. A wall of "maybe
   check the store" is the exact noise the budget kills. A pointer earns its slot
   only if not knowing to query the note would cause a concrete failure — and its
   trailing clause must say which one.

Local memory stays light and the inline/external balance shifts as the codebase
grows: small/young/dormant regions keep everything inline; mature, heavily-grown
regions externalize. `atra-sweep` enforces this with the `over-density` (budget)
and `should-externalize` (growth) findings.

## The register

Inline annotations are the distributed memory. The **register** is its index:
one file (default `docs/atramentous/register.md`, or the project's existing
`docs/scaffolding_register.md`) listing every heavy node — scaffolds,
experiments, decisions, deprecations — with ID, status, location, gate, and risk.
When you add or change a heavy node, update the register in the same change.
`atra-reconcile` keeps them in sync; `atra-map` reads from both.

## Intensity

| Level | What changes |
|---|---|
| **lite** | Breadcrumbs and links only. Heavy blocks only when the user asks. Lightest footprint. |
| **full** | The grammar enforced. Breadcrumbs by default; heavy blocks for spine/scaffold/decision/safety; register kept current. Default. |
| **ultra** | Treat memory loss as the primary failure mode. Every non-trivial decision leaves a node, every scaffold a gate, every spine a guardrail. Use on long-lived, agent-built projects where continuity matters more than footprint. |

## When NOT to leave memory

The discipline cuts both ways — knowing when to stay silent matters as much as
knowing when to record:

- **Recoverable facts.** If the code says it, don't repeat it.
- **Throwaway code.** A one-off script you'll delete this session earns nothing.
- **Volatile specifics that belong in tests.** Don't narrate behavior in prose
  when an assertion pins it precisely. Link to the test instead.
- **Secrets, tokens, personal data.** Memory is durable and committed. Never
  embed anything that shouldn't live forever in version control.
- **Duplicated rationale.** Second copy → make it a link.

Over-annotation is the failure mode. A repo of stale, redundant nodes is worse
than a bare one, because the next agent can't tell signal from noise. Budget.

## Fits alongside other disciplines

Atramentous occupies its own axis and doesn't conflict with whatever governs how
code is written or how work is sequenced:

```
the code itself   → what is the right implementation?
the workflow      → what is the right sequence of steps?
Atramentous       → how will the next agent understand this?
```

The one place to watch is a discipline that says "delete prose longer than the
code." That rule targets *unrequested defensive prose*; Atramentous memory is
*irrecoverable rationale the project asked to keep*. They don't actually
conflict — and the litmus test is the tie-breaker. Fails it → it's prose, delete
it. Passes it → it's memory, it stays, marked as a real node so it never reads as
decoration.

**Where memory work attaches to a development cycle:**

```
after a decision is made    → record it as a node + register entry
while implementing          → leave breadcrumbs and SCAFFOLD blocks as you build
before claiming done        → run atra-review (did any memory get lost?)
before wrapping up the work  → run atra-reconcile (sync memory to reality)
when picking the repo back up → run atra-rehydrate before editing
```

## Proactive surfacing

Memory is worthless if no one reads it at the moment it matters. Don't wait to be
asked — but don't nag. When you enter an area to work, surface what bounds the
work *for that area only*:

- open SCAFFOLD/EXPERIMENT nodes whose gate may now be met,
- DECISION nodes that touch what you're about to change,
- `do-not` / SAFETY guardrails on the code in front of you.

A few high-signal lines, then proceed. The budget applies here too: surfacing the
whole repo's backlog on every task is noise. Surface what's relevant to *this*
edit, offer to act, and never auto-fix. Entropy that accumulates outside the area
you're touching is the scheduled sweep's job (`atra-sweep`), not an interruption
to the current task.

## Working with a human collaborator

The memory budget decides *what to write*. This decides *when to interrupt the
person* — and the default is **don't**. Every decision you hit during work sorts
on two axes: *can I decide this well?* and *must it be decided well now* (versus a
later point that is both cheaper to change and easier to judge)?

```
                    must decide NOW            can WAIT
  decidable     decide; record a DECISION   decide provisionally; SCAFFOLD
                node; proceed               with a gate; proceed (bother no one)
  not           ESCALATE (four-part         SCAFFOLD THE CONSULTATION: a gated
  decidable     format); halt-and-wait      CONSULT at the ripe phase; proceed silently
```

The bottom-right quadrant is where agents fail — they ask too early (nothing real
to judge yet) or never (a silent decision by neglect). Do neither. **Confirming a
decision later is just future scaffolding aimed at a person.** Leave a `CONSULT`
node gated to the phase where it becomes ripe, and proceed:

```kotlin
// ATRAMENTOUS  CONSULT
// why:     panel widths are a feel-call; can't be judged by eye pre-render
// default: 280px side / 1fr main — provisional, in effect now so nothing blocks
// gate:    [[M12 UI Polish]] — batch a human feel-test here
// ask:     do these proportions feel right against the running interface?
```

When `[[M12 UI Polish]]` arrives, the sweep surfaces it and a batch of such
feel-calls go to the human at once, at peak decidability — against a running
interface, not a guess.

**Reversibility prior — this collaborator's stated preference:** *a wrong default
they can correct beats a question they can't yet answer.* Bias hard toward
act-and-report for anything cheap to reverse. But "reversible" includes everything
later built on it: git makes the mechanical undo free, yet a foundation twenty
dependent tasks now assume is **not** cheap to reverse. Confirm load-bearing-but-
early decisions at a *near* checkpoint (a few milestones out, not twenty) via a
scaffolded `CONSULT` — early enough that the blast radius is small, late enough
that there's something real to judge.

**When you do escalate** (must-decide-now *and* genuinely not agent-decidable),
the halt carries four things, in order, or it isn't allowed:

1. what happened (one line);
2. what you already determined — the forensics, done by you, never handed up as a
   chore (reconstruct from git history, surrounding code, the `do-not` clause);
3. what you'll do by default — a concrete recommended action;
4. the one question — phrased so the answer is a judgment/risk/intent call, never
   a fact you could have established yourself.

Test: *could you have answered your own question by working harder?* If yes, it's
risk-offloading, not consultation — go work harder. Reserve escalation for genuine
subjectivity. A `CONSULT` without a `[[named phase]]` gate is "later means never"
wearing politeness; the linter flags it (`consult-gateless`).

## The companions

| Skill | Use it to |
|---|---|
| `atra-weave` | connect a finished piece of work into the graph (back-links + forward-links) |
| `atra-review` | audit for **missing** memory; emits findings, fixes nothing |
| `atra-rehydrate` | reconstruct intent from the memory layer before editing an unfamiliar / resumed repo |
| `atra-reconcile` | promote passed scaffolds, prune dead links, merge dupes, refresh stale rationale, sync the register |
| `atra-map` | generate the navigable atlas from annotations + register |
| `atra-sweep` | autonomously audit for entropy on a timer or on demand; propose fixes, never commit |

Each is independently installable and restates the minimal grammar it needs. The
full grammar lives in `references/grammar.md`. Platform install notes (Cowork /
Codex / Claude Code) are in `references/atra-tools.md`.

## The rule

Leave the repository easier for the next agent to *resume* than you found it.
Clean code is easy to read. Atramentous code is easy to resume. In the age of
agents, the second one is what's scarce.
