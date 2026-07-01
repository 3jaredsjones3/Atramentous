# Atramentous — Behavioral Patterns

These are **moves**, not decorations. Each is something you can *do* to a repo so that
a future agent — arriving cold, with none of your context — behaves differently than it
would have. If a pattern wouldn't change what a later agent does, don't write it.

The distinctive thing Atramentous gives you is **forward-addressed intent and
non-mechanical semantic topology**: not just "here is why this code exists," but
"future agent, here is the unfinished shape of the work, the invariant you must not
break, the research/design rationale you must preserve, and the conceptual neighborhood
the build system cannot see." Mechanical relations — imports, call graphs, test
references — are table stakes; an agent recovers those from the code. The value is in
the relations that leave *no* mechanical trace: work that doesn't exist yet, rules that
span files, and files that belong together conceptually though nothing connects them.

Every example below uses ONLY the existing grammar fields (`why`, `related`, `future`,
`gate`, `promote-when`, `unless`, `risk`, `do-not`, `invariant`, `enforced-by`, `status`,
`default`, `ask`, `local-only`) and the breadcrumb / register / store forms. No pattern
here requires a new field — composing the current ones is the point.

These are intended behavioral patterns. Campaign results may later consolidate, rename,
or retire patterns based on which ones measurably help agents.

These patterns target *different* future-agent behaviors — orientation, refusal,
invariant preservation, plan resumption, handoff quality — and these do not move
together. A campaign may improve one while leaving another unchanged, so any result
should name which behavior it measured rather than report "the patterns helped."

---

## How to use this doc during work

**Start from the behavior you want a future agent to change — not from the field list.**
This is the discipline that keeps Atramentous from becoming a comments-shaped landfill:
if you begin with "which fields apply here," you'll annotate because you can. If you
begin with "what should the next agent do differently," you'll annotate only when there's
a real effect to produce.

Before you write a node, name the move you're making:

- Am I leaving unfinished structure someone will resume? → **Forward Scaffold (1)**
- Am I preserving a rule that spans files? → **Cross-File Invariant (2)**
- Am I preventing a confident wrong refactor? → **Obvious-Local-Fix Warning (3)**
- Am I marking when incomplete work becomes safe to finish? → **Promotion Gate (4)**
- Is the system hard to enter cold? → **Cold-Start Rehydration Path (5)**
- Is awkward-looking code actually a compatibility promise? → **Temporary Compromise (6)**
- Is this guardrail important enough that prose isn't enough? → **Bind to Enforcement (7)**
- Will two files depend on each other conceptually before they do mechanically? →
  **Link to Future Structure (8)**
- Do several files form one design idea that editing singly would break? →
  **Semantic Cluster (9)**
- Is this code the residue of research/design/math reasoning a future agent would
  "simplify" away? → **Research Grounding (10)**

If none of these is the move, you probably don't need a node — you need a comment, or
nothing. Pick the move, then fill the fields the move needs. Never the reverse.

---

## 1. Leave a forward scaffold for unwritten work

**When:** you're shipping something deliberately partial and you know what the next
piece is, but it's not time to build it.

```ts
// ATRAMENTOUS SCAFFOLD [[Worker Backpressure]]
// why:    the queue assumes a single producer; once parallel workers can enqueue,
//         contention needs an explicit pressure boundary, not ad-hoc throttling.
// future: [[src/workers/backpressure.ts]]
// gate:   promote when enqueue() can be called from more than one worker source.
// do-not: hide backpressure inside retry-delay logic — retries and pressure are
//         separate mechanisms and conflating them makes both unfixable.
// invariant: a full queue must reject or block, never silently drop a job.
```

**Future-agent behavior:** a later agent adding parallel workers finds the boundary
already named, builds `backpressure.ts` instead of bolting throttling onto retries, and
knows the one thing it must not do. It resumes a plan instead of inventing one.

---

## 2. Mark a cross-file invariant

**When:** the rule that matters spans more than the file you're in, so a local reader
can't see it.

```py
# ATRAMENTOUS SPINE [[Active-Path Branch Reconstruction]]
# why:       tree=True returns ALL branches; index overlaps across branches.
# invariant: the active path is defined SOLELY by walking parent_message_uuid links;
#            NO field-based ordering is valid.
# do-not:    sort candidate messages by index, timestamp, orderHint, or array order to
#            reconstruct the branch — any sort leaks sibling branches.
# related:   [[tests/active-path.spec.js]]
# enforced-by: [[test:active-path-branch-purity]]
```

**Future-agent behavior:** an agent "improving" ordering reads the invariant before
touching the sort, sees the prohibition is the *principle* (no field ordering) not a
list it can slip around, and that a test will fail if it tries. The rule travels to the
file even though it's about three.

---

## 3. Warn against the obvious local fix

**When:** the code looks like it's begging for a simplification that would quietly break
a wider contract.

```rs
// ATRAMENTOUS SAFETY [[Ignore-Rule Precedence]]
// why:      this reads like a local filter, but the ORDER here defines global ignore
//           semantics — explicit CLI includes must override project ignore files, but
//           not hard excludes.
// invariant: precedence is CLI-include > ignore-file > hard-exclude, in that order.
// do-not:   collapse this into a single boolean predicate unless the precedence tests
//           are updated first; the layering is the feature, not accidental complexity.
// enforced-by: [[test:ignore-precedence]]
```

**Future-agent behavior:** the agent that would have "cleaned up" the nested conditions
into one clause stops, because the note tells it the mess is load-bearing and names the
test that guards it. This is the single highest-value Atramentous move — it prevents the
confident wrong refactor.

---

## 4. Define a promotion gate for incomplete work

**When:** something is intentionally not-yet-done and cleaning it up early would be a
mistake. State the condition that makes cleanup safe.

```js
// ATRAMENTOUS SCAFFOLD [[Renderer Measurement Split]]
// why:        width calculation and ANSI span emission are still coupled here.
// future:     [[src/render/measure.js]] [[src/render/emit.js]]
// gate:       split only after snapshot tests cover nested styles AND zero-width spans.
// unless:     a rendering bug forces an earlier split — then split, but port the
//             coupling tests first.
// risk:       bugs here are visually silent; a wrong split won't throw, it'll just
//             render subtly wrong, so don't trust "it runs" as proof.
```

**Future-agent behavior:** instead of either rotting forever or being split prematurely,
the scaffold tells a future agent the exact precondition for action — and `risk:` warns
it not to trust a clean run as evidence of correctness.

---

## 5. Give a cold-start rehydration path

**When:** behavior is distributed across several files and there's a *right order* to
read them in. Encode the order so the next agent doesn't reconstruct it by grep.

```md
<!-- ATRAMENTOUS REFERENCE [[Auth Flow Map]] -->
<!-- why: auth behavior is split across session state, refresh timing, and request
     retry; editing retry without the other two causes silent token-expiry loops. -->
<!-- related: [[src/auth/session.ts]] -->
<!-- related: [[src/auth/token-refresh.ts]] -->
<!-- related: [[src/http/interceptors.ts]] -->
```

**Future-agent behavior:** an agent asked to change retry behavior reads the three files
in the stated order first, and avoids the silent-loop bug that comes from editing one
corner of a three-corner system. The reading order is the deliverable; the links are
ordered on purpose.

*(Note: the register at `docs/atramentous/register.md` is the canonical place for a map
that spans the whole repo. Use an inline REFERENCE block like this for a local cluster;
use the register for the repo-wide index.)*

---

## 6. Record a temporary compromise

**When:** the code is shaped awkwardly for a real external reason, and a future agent
would "fix" it without knowing the reason.

```go
// ATRAMENTOUS REFERENCE [[CLI Output Compatibility]]
// why:    this output shape is awkward because scripts in the wild parse it by field
//         position; the awkwardness is a compatibility contract, not sloppiness.
// invariant: field ORDER is stable API; humans-readability is intentionally subordinate.
// do-not: reorder or rename output fields unless docs/cli-output.md's compatibility
//         note is updated and a major version is cut.
```

**Future-agent behavior:** the agent that would have "tidied" the output for readability
learns the ugliness is a promise to downstream parsers, and leaves it — or does the
real, versioned thing instead of the silent breaking change.

---

## 7. Bind rationale to enforcement

**When:** a guardrail matters enough that prose alone is too weak — a later agent could
read past it. Point at the thing that *fails* when the rule is broken.

```py
# ATRAMENTOUS SAFETY [[Money Rounding]]
# why:       currency math must round half-to-even at the boundary, not per-operation,
#            or totals drift by cents over many lines.
# invariant: round ONCE, at presentation, banker's rounding; never mid-calculation.
# do-not:    insert round() calls inside the accumulation loop.
# enforced-by: [[test:invoice-total-rounding]]
```

**Future-agent behavior:** prose informs a cooperative reader; `enforced-by:` binds an
uncooperative one. An agent that ignores the comment still trips the test. Use this on
the guardrails where being read-past would actually hurt.

---

## 8. Link existing code to future structure

**When:** two files don't depend on each other *mechanically* yet, but will *conceptually*
soon — and a future agent editing one needs to know the other is coming.

```ts
// atra: [[Rate Limiter]] → [[src/middleware/quota.ts]] — quota.ts will consume the
// same token-bucket state this limiter owns; keep the bucket interface stable.
```

**Future-agent behavior:** an agent refactoring the rate limiter's internal state sees
that an unwritten consumer is already planned against its interface, and keeps that
interface stable instead of optimizing it into a shape the future file can't use. This
is the forward link in its lightest form — a breadcrumb to territory not yet built.

---

## 9. Map a semantic cluster the build system can't see

**When:** several files express one design idea, but nothing imports anything — so an
agent tuning one in isolation could wreck the whole, and no dependency tool would warn
it. The guard against link-spam: only write this when **editing one member in isolation
has a non-local consequence**, not merely when files "feel related."

```ts
// ATRAMENTOUS REFERENCE [[Aim-Assist Feel Model]]
// why:     input smoothing, target magnetism, and reticle easing implement ONE UX feel
//          model, even though they live in separate systems and don't reference each other.
// related: [[src/input/smoothing.ts]]
// related: [[src/combat/target-magnetism.ts]]
// related: [[src/ui/reticle-ease.ts]]
// related: [[research/aim-assist-feel-notes.md]]
// risk:    tuning one file alone can improve a local metric while making the whole feel
//          model inconsistent — these must be reasoned about together, not edited singly.
```

**Future-agent behavior:** an agent asked to "make aiming snappier" inspects the whole
conceptual neighborhood instead of locally cranking one magnetism constant, because the
node tells it the three files are one system. The `risk:` line is what earns the node —
without a stated non-local consequence, "these are related" is decoration. This is the
relation Atramentous exists for: conceptual dependency with no mechanical trace.

---

## 10. Ground implementation in its research / design / math rationale

**When:** the code is the executable residue of reasoning that lives *outside* the
repo — a derivation, a UX study, a design decision — and a future agent would "simplify"
it into a generic plausible version because nothing in the code says it was bespoke on
purpose. Agents love plausible simplifications; this is the guard against them.

```py
# ATRAMENTOUS REFERENCE [[Bezier Camera Ease]]
# why:       this camera easing curve follows the perceptual-overshoot notes in the UX
#            research file, NOT a generic cubic ease — the shape is intentional.
# related:   [[research/camera-motion-ux.md]]
# related:   [[notebooks/easing-curve-fit.ipynb]]
# invariant: preserve monotonic entry and sub-8% overshoot unless the UX target changes.
# do-not:    replace with a stock easing preset just because it has fewer parameters.
```

**Future-agent behavior:** the agent that would have swapped the bespoke curve for
`easeOutCubic` ("this is overcomplicated") instead sees that the shape encodes a design
rationale it must preserve, and changes it only if the UX target itself changes. The
node connects the code to the *reasoning substrate that produced it* — the most
context-window-mortal thing of all, because it often isn't even in the repo.

---

## Anti-patterns (do NOT do these)

- **Don't annotate recoverable facts.** If `grep` or reading the function answers it,
  it doesn't need a node. Atramentous is for what *dies* with the context window.
- **Don't use it as a TODO graveyard.** A scaffold without a `gate:` is just a TODO with
  ceremony. If you can't state the promotion condition, you're not ready to leave a
  scaffold — leave a `future:` breadcrumb or nothing.
- **Don't create links without behavioral purpose.** A `[[link]]` that doesn't change
  what a future agent reads or does is noise. Every link should answer "and the next
  agent should therefore ___."
- **Don't map a "semantic cluster" that's just vibes.** Files being thematically similar
  is not enough. A cluster node earns its place only when editing one member in isolation
  has a *non-local consequence* the build system can't see — state that consequence
  (usually in `risk:`), or don't write the node. "These are related" is the easiest
  decoration to write and the easiest rot to accumulate.
- **Don't enumerate instead of stating the invariant.** A `do-not:` that lists specific
  forbidden things has gaps a literal reader walks through. Pair it with `invariant:`
  that states the *rule*. (The linter's `do-not-needs-invariant` enforces the pairing.)
- **Don't duplicate the local line.** A comment that restates what the adjacent code
  obviously does is rot. The node earns its place only if it carries something the code
  cannot say for itself — intent, hazard, future shape, cross-file reach.
- **Don't externalize a guardrail.** A SAFETY/SPINE rule belongs inline, next to the
  code it governs, or relocated onto the nearest file on the access path — never behind
  a pointer the reader might not follow.

---

## Pattern selection (quick reference)

When you're under context pressure and need to pick fast — match the *risk* you see to
the move:

| If the risk is… | Use |
|---|---|
| Premature cleanup of intentionally-partial work | Promotion Gate (4) |
| A wrong local simplification that breaks a wider contract | Obvious-Local-Fix Warning (3) |
| The next thing doesn't exist yet | Forward Scaffold (1) |
| The rule spans files a local reader can't see | Cross-File Invariant (2) |
| The system is hard to enter cold | Cold-Start Rehydration Path (5) |
| Awkward code is secretly a compatibility promise | Temporary Compromise (6) |
| A guardrail that prose alone is too weak to hold | Bind to Enforcement (7) |
| A coming dependency that isn't mechanical yet | Link to Future Structure (8) |
| Files that are one design idea but editing one breaks the whole | Semantic Cluster (9) |
| Code whose shape comes from external research/design a future agent would simplify away | Research Grounding (10) |

---

## The question before you write Atramentous

Before you leave a node, ask:

1. **Would a future agent behave differently because this exists?** If no — delete it.
2. **Does it preserve intent that would otherwise die with the context window?** If the
   information survives in code, tests, or git, it doesn't need a node.
3. **Does it point to a future action, a hazard, an invariant, or a reading path?** If
   it's none of these, it's probably a comment, not an Atramentous node.

If a node passes all three, it's earning its place. If it fails any, it's decoration —
and decoration is the thing this system exists to *not* become.
