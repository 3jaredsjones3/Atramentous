# Atramentous Test-Campaign Protocol (for a context-free orchestrator)

You are being handed this document with NO other context. It tells you two things:
(1) what Atramentous is, so you can do the annotation work and understand what is
being measured; (2) the exact experimental process to run, stage by stage, with the
blinding rules that keep the result valid. Read all of Part 0 before acting — it
contains the one rule that, if broken, silently invalidates everything.

---

# PART 0 — THE RULE THAT MATTERS MOST (read first)

This experiment measures whether embedding intent-memory in code helps a later AI
agent avoid mistakes. It works by comparing the SAME code in three versions that
differ ONLY in how much memory-annotation they carry. The comparison is only valid
if the stages below stay **isolated** — i.e. the chat doing one stage must not know
information that belongs to another stage. The classic way this breaks: one model
helpfully does everything in a single conversation, and its knowledge of the answer
leaks into the task it picks, the code it grades, or the arm it runs.

**THEREFORE: each numbered STAGE below must be run in a SEPARATE chat / session, and
each stage's prompt explicitly states what that chat is FORBIDDEN to know.** Do not
merge stages to save effort. If you (the model reading this) are tempted to "just do
the next stage too since you have context," that temptation is the failure mode. The
walls are the experiment.

The blinding walls, summarized (details in each stage):
- The **annotator** (Stage 3) must NOT know what task will be run.
- The **task-picker** (Stage 5a) must NOT see the annotations.
- The **task-runner** (Stage 7) must NOT know which arm it is running.
- The **grader** (Stage 8) must NOT know the hypothesis, the arms, or which is which.

A human (the experimenter) holds the keys between stages and runs local terminal
commands where needed (git clone, etc. — see the GIT NOTE below). You generate the
commands and the artifacts; the human executes the privileged steps and keeps the
codename key. Never ask to see the codename key.

GIT NOTE: you may not be able to fork/create repos directly. That's fine and
expected. Whenever a stage needs a repo cloned, stripped, or pushed, you OUTPUT the
exact terminal commands (PowerShell + git, or a Python script) and the human runs
them locally where credentials and the filesystem live. Treat "the human runs my
clone/strip commands" as a normal step, not a blocker. Repos are cloned manually;
prepare batch scripts if many test repos are being set up at once.

---

# PART 1 — WHAT ATRAMENTOUS IS (so you can do the annotation stage)

Atramentous is a convention for embedding an AI agent's reasoning INTO the source
tree, so a future agent (which has no memory of past sessions) can reconstruct
*why* the code is the way it is without re-deriving it. The core bet: most agent
coding failures are not "the model wasn't smart enough" but "the model didn't have
the relevant intent in front of it at the moment of decision." Atramentous delivers
that intent in-place.

It works through annotations placed as comments beside the code they explain:

**A heavy block** (for load-bearing rationale or a guardrail):
```
// ATRAMENTOUS  SPINE
// why:       <the durable reason this code is shaped this way>
// invariant: <the GENERAL rule that must hold — state the principle, not just
//             a list of forbidden actions>
// do-not:    <specific forbidden actions — but ALWAYS pair with the invariant
//             above, because a list of instances has gaps a literal reader falls
//             through; the invariant closes them>
// related:   [[Some Named Node]]
```

Status keywords mark lifecycle/role: SPINE (load-bearing structural truth), SAFETY
(a guardrail whose violation causes real harm), SCAFFOLD (temporary), DECISION
(a recorded choice), REFERENCE, EXPERIMENT.

**A lightweight breadcrumb** (just a semantic link):
```
// atra: [[Target Node]] — <one line on why this connection matters>
```

**A pointer to externalized memory** (when the rationale is too heavy to inline, it
lives in docs/atramentous/store/<slug>.md and the code carries only):
```
// atra: see [[store:<slug>]] — <the concrete failure that happens if you don't read it>
```

Key principles you must honor when annotating:
- **Guardrails (SAFETY/SPINE/do-not) capture the things a plausible-looking change
  would silently break** — ordering constraints, invariants, workarounds, non-obvious
  reasons. Annotate the LOAD-BEARING and NON-OBVIOUS, not the self-evident.
- **State invariants, not just instances.** A `do-not` that lists specific fields or
  functions has gaps; always pair it with an `invariant:` line stating the general
  rule. (This rule exists because a real test showed an agent walk through the gap
  in an enumerated prohibition.)
- **Files that can't hold comments** (CSV, JSON, generated files, or product
  artifacts where a comment would corrupt the output) are "external-only": their
  memory goes in the store, and a pointer is placed on the nearest code file that an
  agent would pass through to reach them.
- Annotate the WHOLE repo on its merits. (Critical: see Stage 3's blinding rule.)

---

# PART 2 — WHAT IS BEING MEASURED (so you understand the point)

Three versions ("arms") of the identical repo are compared:
- **Arm A (bare):** no annotations at all. The control.
- **Arm B (links-only):** only the bare [[links]] survive — connections, but no
  rationale, no guardrails, no prose.
- **Arm C (full):** the complete Atramentous web.

A fresh agent runs the SAME task on each arm. Two gaps are the result:
- (B − A) = does bare connectivity alone help?
- (C − B) = does the full rationale/guardrail layer add value beyond mere links?

The task is deliberately chosen to touch code with a NON-OBVIOUS hidden constraint —
a place where an uninformed agent would make a wrong-but-plausible-looking change.
The measurement is: did each arm's agent preserve the hidden invariant, and did its
own (pre-task) statement of the project's constraints show it understood them.

---

# PART 3 — THE STAGES (each in a SEPARATE chat unless noted)

## STAGE 0 — Build & self-test the pipeline scripts (one chat; you may build freely)
Write reusable scripts and PROVE them on synthetic data before any real repo:
- `strip_full.py` — removes ALL Atramentous content (ATRAMENTOUS blocks, `atra:`
  lines, bare `[[...]]`-only comment lines, and docs/atramentous/). Must NOT touch
  ordinary code or ordinary comments. The test for "is this an annotation": the line
  is a comment AND contains "ATRAMENTOUS", or starts with `atra:`, or is a comment
  whose entire payload is only [[...]] tokens. Code that merely contains `[[` (regex
  literals, template strings) is NOT an annotation — leave it.
- `strip_links_only.py` — reduces each annotation to ONLY its [[...]] tokens on one
  comment line; removes all prose/why/guardrail/status. Same code-safety rule.
- `verify.py` — given arms A/B/C and the original, confirm (a) all three have
  byte-identical CODE lines (everything that isn't an annotation), and (b) arm A's
  code matches the original (proves annotation was additive). Emits PASS/FAIL with
  exact diffs.
- `codename.py` — given A/B/C, assign random codenames (e.g. Venus/Saturn/Earth),
  output the codenamed copies AND a `key.json` (codename→arm). The key is for the
  HUMAN only.
- `manifest.py` — hash every file; used to detect truncation/corruption at every
  later handoff.

SELF-TEST (mandatory before trusting any of these): construct synthetic input with a
known-correct expected output — including a file that contains `[[` inside real code
— run the whole chain, and confirm strip doesn't touch code, verify catches an
injected code-difference, and codename/key round-trips. Report the self-test result.
Do not proceed to a real campaign until the scripts pass on synthetic data.

## STAGE 1 — Acquire & clean (you generate commands; human runs them)
Output terminal commands (PowerShell + git, or a Python batch script) to clone the
chosen public repo locally into the experimenter's test folder, then strip
`node_modules/`, `.git/`, and build artifacts, and normalize line endings. Run
`manifest.py` to produce the canonical tree + hashes. (You generate; the human runs,
because cloning needs local credentials.)

## STAGE 2 — Confound scan (you analyze the clean tree)
Scan for things that would confound the experiment and report them in `confounds.md`:
- duplicate files where one is dead/unloaded (an agent may edit the wrong one),
- generated files, ambiguous entry points, anything that determines "which file is
  actually live." The human decides whether to remove a dead duplicate or keep it.
(This stage exists because a prior run was wrecked by agents editing a dead-duplicate
file the program never loaded.)

## STAGE 3 — Annotate → produces Arm C  (SEPARATE CHAT — TASK-BLIND)
**This chat must NOT be told what task will later be run.** Annotate the whole clean
repo on its own merits, per Part 1. Produce the fully-annotated tree (Arm C) and an
`annotation-provenance.md` recording that YOU (model name + date) authored the
annotations. (Why this matters: anything in the annotation layer is YOUR cognition,
not the running agent's, and must never later be read as evidence of what the running
agent understood. And if you knew the task, you'd unconsciously annotate toward it,
making Arm C unfairly strong exactly where it's tested.)

## STAGE 4 — Derive Arms B and A  (scripts; mechanical)
Run `strip_links_only.py` on Arm C → Arm B. Run `strip_full.py` on Arm C → Arm A.
Run `verify.py` across A/B/C + original. If verify FAILS (code lines differ, or A
doesn't match original), STOP and report — the annotation pass was not additive, or a
strip touched code. Do not run the experiment on unverified arms.

## STAGE 5 — Task selection (TWO separate roles)
**5a (SEPARATE CHAT — ANNOTATION-BLIND):** give this chat ONLY Arm A (bare code).
Ask it to propose a POOL of 3–5 candidate tasks that each: modify/extend existing
code (not a standalone new feature), touch code with non-obvious hidden intent (a
place a plausible change could silently break something), are bounded to one session,
and are genuinely useful. Output the pool with a one-line "where the hidden-reason
risk lives" per task. This chat must NOT see Arm C.
**5b (sighted filter — human, or a chat shown Arm C that ONLY subtracts):** from the
pool, REJECT tasks that won't discriminate or that land on a dead-duplicate. The
filter may reject but must NOT author or reword a task. Freeze the surviving task
verbatim to `task.md`. (Rationale: a blind picker is fair but may pick something
trivial; a sighted picker is discriminating but biased. Blind proposes, sighted only
subtracts — so the task is fair in origin and hard enough to matter.)

## STAGE 6 — Pre-task comprehension capture (per run, BEFORE code)
Each running agent, before touching any code, answers in its OWN words: "What is this
project, what are its load-bearing constraints, and what are you unsure about?"
Capture verbatim to a file per run. (This is the ONLY valid evidence of what the
RUNNING agent understood — distinct from the annotations it inherited.)

## STAGE 7 — Run the task  (SEPARATE COLD SESSIONS — ARM-BLIND)
Hand each codenamed arm (from `codename.py`) to a FRESH, isolated agent session that
is NOT told which arm it holds. Same frozen `task.md` for all. ≥3 runs per arm
(more runs = more signal; a single run per arm proves nothing). Each run does Stage 6
first, then the task, then saves its result. The human assigns codenames via the key;
no runner sees the key. (These runs are typically executed by a local coding agent —
Cowork/Codex — driven by commands you can help generate; the human runs them.)

## STAGE 8 — Grade  (SEPARATE CHAT — HYPOTHESIS-BLIND)
The rubric is authored ONCE by someone who knows the hidden invariant (the human, or
a sighted helper) into `rubric.md`, with a MECHANICAL pass/fail criterion (e.g.
"PRESERVED = the invariant still holds in the code; BROKEN = it was violated"). A
FRESH chat that knows nothing about arms, hypothesis, or codename meanings grades the
codenamed results against `rubric.md`. Score each result independently (do NOT rank
them against each other). Also run any mechanical invariant-test script for the
primary metric so the headline number is outside model judgment. Run the grader TWICE
(re-shuffled) and check the calls agree.

## STAGE 9 — Collate & unblind  (human opens the key LAST)
Only after every grade is frozen, the human opens `key.json` and joins codename→arm.
Produce the grid: per-arm invariant-preserved rate, the (B−A) and (C−B) gaps, the
Stage-6 comprehension scores, and a failure-mode note for any broken arm. Record
confounds and n honestly. With ~3 runs/arm the result is DIRECTIONAL, not
statistically powered — report raw counts (2/3), not percentages, and say so.

---

# PART 4 — STANDING DISCIPLINE

- Verify every artifact against the manifest at every handoff. A truncated or
  mis-zipped file must fail loudly here, not surface three grading passes later.
- The codename key is opened only at Stage 9. Never request it earlier.
- "Better than doing nothing" is the bar for the memory system: if a result is null
  or negative, report it plainly — a failed prediction is a real finding, and a
  cleanly negative result is more valuable than a narrated win.
- If any stage's blinding wall was crossed (a chat saw what it shouldn't), the run is
  compromised — say so rather than reporting it as clean.
