# Atramentous Experiment Toolkit — BUILD SPEC

You are building a small toolkit of Python scripts that let a human run many blind
A/B/C experiments without losing track of state or accidentally breaking the
blinding. This document tells you exactly what to build. Build ALL of it, then run
the synthetic self-test in Part E and report the result. Do not skip the self-test —
an unvalidated pipeline silently manufactures invalid results.

Companion document: "Atramentous Test-Campaign Protocol" defines the experiment and
the stages. This document defines the SCRIPTS those stages call. Build to this spec;
where they overlap, this spec governs script behavior.

Target: Python 3, standard library only where possible (no heavy deps). Cross-platform
(the human is on Windows; use pathlib, avoid shell-isms). Every script is runnable as
`python <script>.py <args>` and prints a clear PASS/FAIL or summary line.

---

## DESIGN PRINCIPLES (these shape every script)

1. **The human holds no mutable state in their head.** State lives in `STATE.md` per
   test. Every script, on success, UPDATES that test's STATE.md (checks its line,
   records the artifact path). The human's only navigation rule is "open STATE.md,
   do the first unchecked line."
2. **Blinding is enforced by the filesystem, not by discipline.** Identity (which
   arm) lives only in `blind/key.json`, which the human is told never to open until
   Stage 9. Scripts that hand work outward emit codename-only instructions.
3. **Fail loud, fail early.** verify and manifest checks STOP the pipeline on any
   mismatch. A truncated/reformatted/contaminated artifact must fail at the handoff
   that produced it, not three stages later.
4. **General, not per-repo.** All scripts work on any repo by keying off structure
   (annotation syntax, file hashes), not repo content. The ONLY per-repo input is
   `confounds.json`, which an LLM produces by analysis.

---

## FOLDER LAYOUT (the scripts assume and create this)

```
Tests/
  _pipeline/                       # the scripts themselves live here
  T<NNN>_<slug>/                   # one folder per test
    STATE.md                       # single source of truth for this test
    00_clean/                      # canonical cleaned repo
      manifest.sha256
    confounds.json                 # per-repo, LLM-produced, human-approved
    arm_C/  arm_B/  arm_A/         # the three arms (never handed out under these names)
    blind/
      <codename1>/ <codename2>/ <codename3>/   # codenamed copies = what gets handed out
      key.json                     # codename->arm. HUMAN-TABOO until Stage 9.
      RUN_INSTRUCTIONS.md          # codename-only run checklist
    task.md
    rubric.md
    runs/
      <codename>_run<n>/           # each: the modified repo + comprehension.txt
    grades/
    RESULT.md
```

---

## PART A — SCRIPTS THAT MANAGE STATE & SCAFFOLDING

### A1. `new_test.py <test_id> <slug> <repo_url>`
Creates `Tests/T<id>_<slug>/` with the full subfolder skeleton above (empty) and a
fresh `STATE.md` from the template in Part D. Records repo_url in STATE.md. Refuses
to overwrite an existing test folder. Prints the created path.

### A2. `state.py <test_dir> [--check <stage_id> <note>]`
- With no flags: prints the test's STATE.md.
- With `--check S4 "verify PASS"`: marks stage S4 done in STATE.md, appends the note
  and a timestamp. (Other scripts call this internally on success — but it's also
  runnable by the human.)
Parsing rule: STATE.md stage lines look like `[ ] S4 ...` / `[x] S4 ...`. Editing
flips the box and appends ` — <note> (<ISO timestamp>)`.

### A3. `status.py [Tests/]`
THE DASHBOARD. Scans every `T*/STATE.md` and prints one line per test: test id, the
first unchecked stage ("arrow"), run progress if in S6/7 (e.g. "4/9 runs"), and a
loud flag if any stage recorded a FAIL/BLOCKED. Example output:
```
T007_fastapi    -> S5 task selection        (S1-4 done)
T008_excalidraw -> S7 runs                   (4/9 runs done)
T009_tldraw     !! BLOCKED at S4 (verify FAILED) 
```
This is the human's one-command "where is everything." Make it scannable.

---

## PART B — SCRIPTS THAT BUILD & BLIND THE ARMS

### B1. `manifest.py <dir> [--verify <manifest_file>]`
- Default: walk `<dir>`, write `manifest.sha256` = sorted `relpath  sha256` for every
  file (skip `.git/`, `node_modules/`). Print file count.
- `--verify`: recompute and compare against an existing manifest; print PASS or list
  every added/removed/changed file and exit nonzero. Used at every handoff to catch
  truncation/corruption.

### B2. `clean.py <raw_repo_dir> <out_dir>`  (or emit a script — see note)
Strips `node_modules/`, `.git/`, common build dirs (`dist/`, `build/`, `.next/`,
etc.), and normalizes line endings to LF. Writes the result to `00_clean/` and calls
manifest.py on it. NOTE: cloning needs the human's credentials, so cloning itself is
NOT in this script — `clean.py` operates on an already-cloned tree. Also provide a
`clone_and_clean.ps1` TEMPLATE the human runs (it `git clone`s then calls clean.py).

### B3. `strip_full.py <in_dir> <out_dir>`
Produces ARM A. Removes ALL Atramentous content, leaving code byte-identical:
- Remove any comment line containing the token `ATRAMENTOUS` AND its immediately
  following continuation comment lines (lines that are comments and match the field
  grammar: why/invariant/related/future/gate/promote-when/unless/risk/do-not/status/
  default/ask/local-only/annotate/enforced-by).
- Remove any comment line whose content starts with `atra:`.
- Remove any comment line whose ENTIRE payload is only `[[...]]` tokens + whitespace.
- Remove the `docs/atramentous/` directory.
CODE-SAFETY (critical): a line is only an annotation if it is a COMMENT and matches
above. Code that merely CONTAINS `[[` (regex literals like `/\[\[\^\]\]/`, template
strings like `'[[Attachment]]'`, destructuring) is NOT an annotation — leave it
untouched. Never remove an ordinary code comment that lacks the ATRAMENTOUS/atra:
markers and isn't a pure-link comment. Do not reflow, reindent, or collapse code.

### B4. `strip_links_only.py <in_dir> <out_dir>`
Produces ARM B. For each Atramentous block, REPLACE it with a single comment line
containing only its `[[...]]` tokens; remove all prose/why/invariant/guardrail/status.
If a block has no `[[...]]` token, remove it entirely. Same CODE-SAFETY rule as B3 —
never touch code or ordinary comments. One uniform rule applied everywhere.

### B5. `verify.py <original_clean> <arm_A> <arm_B> <arm_C>`
THE GATE. Confirms the arms differ ONLY in annotations:
- Extract "code lines" from each arm = every line that is NOT an Atramentous
  annotation or pure-link comment (reuse B3/B4's classifier). Assert code lines are
  identical across A, B, C. 
- Assert arm_A's full content == original_clean (proves the annotation pass was
  additive — no code was touched during annotation).
- Report PASS, or print the exact offending file + line diffs and exit nonzero.
On PASS, calls state.py to check the S4 line. On FAIL, records "S4 verify FAILED" in
STATE.md so status.py flags it.

### B6. `codename.py <arm_A> <arm_B> <arm_C> <blind_dir> <task_file>`
THE BLINDING STEP. 
- Randomly maps {arm_A,arm_B,arm_C} -> 3 codenames (default pool: a rotating list of
  neutral codenames; never reuse the SAME mapping across tests — randomize per test).
- Copies each arm into `blind/<codename>/`, but FIRST scrubs identity leaks from each
  copy: delete any agent-authored summary/report/notes files (`*SUMMARY*.md`,
  `*CHANGES*.md`, `ACTIVEPATH*.md`, `annotation-provenance.md`, etc.), and assert (via
  the B3 classifier) that arm_A/arm_B copies contain no residual full ATRAMENTOUS
  blocks. (Arm C keeps its annotations — it's supposed to have them — but its
  provenance/report files are still scrubbed so the codename can't be inferred from a
  filename.)
- Writes `blind/key.json` = {codename: arm}. 
- Writes `blind/RUN_INSTRUCTIONS.md` — codename-only: "For each of <codenames>: (1)
  capture comprehension.txt by answering the pre-task question BEFORE editing; (2)
  run the task in task.md; (3) save the modified repo to runs/<codename>_run<n>/.
  Do 3 runs per codename." It must NOT mention arms, annotations, or the hypothesis.
- Prints ONLY the codenames (never the mapping) to stdout, so the human running it
  doesn't see the key.

---

## PART C — SCRIPTS THAT GRADE & COLLATE

### C1. `invariant_test.py <runs_dir> --check <check_module>`
The MECHANICAL primary metric. For each `runs/<codename>_run<n>/`, run a per-campaign
invariant check (supplied per experiment as a small Python predicate file — the human
or a sighted helper writes it once, knowing the hidden invariant) that reads the
relevant file and returns PRESERVED / BROKEN / ENGAGED-NO. Emit `grades/mechanical.csv`
with codename, run, engaged, preserved. No model needed; no arm identity used.
Provide a template `check_TEMPLATE.py` showing the predicate signature.

### C2. `make_grader_bundle.py <test_dir> <out_zip>`
Packages EXACTLY what the blind grader chat may see: the codenamed `runs/`, `task.md`,
`rubric.md`. ASSERTS that `key.json` is NOT included (refuse to build the bundle if it
would be). This prevents the #1 grading leak — the key ending up in the grader's
upload. Print what's included.

### C3. `collate.py <test_dir>`
Stage 9 — the ONLY script that opens `key.json`. Joins codename->arm across
mechanical.csv and any model-grader scores the human drops in `grades/`. Writes
`RESULT.md`: per-arm preserved rate (raw counts like 2/3, not percentages),
the (B-A) and (C-B) gaps, comprehension-score summary, n, and a "DIRECTIONAL not
powered" caveat line. Marks S9 done.

---

## PART D — THE STATE.md TEMPLATE (new_test.py writes this)

```
# T<id> <slug> — STATE
repo: <repo_url>
created: <iso>

[ ] S1 clone & clean        (-> 00_clean/, manifest)
[ ] S2 confounds scanned    (-> confounds.json, human-approved)
[ ] S3 annotated -> arm_C   (annotator + date in annotation-provenance.md)
[ ] S4 arms derived + VERIFIED  (verify.py must PASS)
[ ] S5 task chosen          (blind-propose 5a, sighted-subtract 5b -> task.md)
[ ] S6/7 runs               (need 3/arm = 9; RUN_INSTRUCTIONS.md drives this)
[ ] S8 graded               (invariant_test.py + blind grader bundle)
[ ] S9 unblinded -> RESULT.md

## human-judgment log (fill as you go)
- confounds decision:
- task chosen:
- anything weird:
```

---

## PART E — SYNTHETIC SELF-TEST (build this, run it, report result BEFORE real use)

Create `selftest/` with a tiny fake repo (3-4 source files in a couple languages)
that deliberately includes the hard cases:
- a real ATRAMENTOUS block (with why/invariant/do-not),
- an `atra:` breadcrumb,
- a bare `// [[Link]]` comment,
- a `// [[store:x]]` pointer,
- an ORDINARY code comment (must survive stripping),
- a line of real CODE containing `[[` (e.g. a regex literal `/\[\[\^\]\]/` and a
  template string `'[[Attachment]]'`) that must NOT be touched,
- a docs/atramentous/ store note.

Then assert, in `selftest.py`:
1. strip_full produces code byte-identical to a hand-made expected "bare" version;
   the ordinary comment survives; the `[[`-bearing CODE lines survive untouched;
   docs/atramentous/ is gone.
2. strip_links_only keeps only the `[[...]]` tokens; prose/guardrails gone; the
   `[[`-bearing code lines still untouched.
3. verify PASSES on (clean, A, B, C) built from the fixture, and verify FAILS when
   you inject a one-character change into arm_B's CODE (proves verify catches drift).
4. codename produces 3 codenamed dirs + key.json, the key round-trips
   (collate can recover the mapping), the codenamed arm_A/B dirs contain no residual
   ATRAMENTOUS blocks, and stdout never printed the mapping.
5. make_grader_bundle REFUSES when key.json would be included.

Report: each of the 5 self-tests PASS/FAIL, and do not declare the toolkit ready
unless all pass. If any fails, fix and re-run.

---

## PART F — THE HUMAN'S OPERATING LOOP (put this at the top of STATE-driven use)

Once the toolkit passes self-test, a full test run is:
1. `python new_test.py 007 fastapi <url>`  → scaffold + STATE.md
2. paste the `clone_and_clean` script (clones with your creds, then clean.py runs)
3. (new chat) LLM writes confounds.json from the repo → you approve → delete dead dups
4. (new TASK-BLIND chat) LLM annotates 00_clean → drop into arm_C/  (+ provenance)
5. `python strip_links_only.py … ; python strip_full.py … ; python verify.py …`
   — if verify FAILS, stop and fix S3.
6. (new ANNOTATION-BLIND chat, given only arm_A) propose task pool → you subtract →
   freeze task.md
7. `python codename.py …`  → follow blind/RUN_INSTRUCTIONS.md to launch the 9 runs
   in your local coding agent (codenames only — you never act on arm identity)
8. `python invariant_test.py …` ; `python make_grader_bundle.py …` → hand bundle to a
   fresh HYPOTHESIS-BLIND grader chat → drop its scores in grades/
9. `python collate.py …`  → RESULT.md  (this is when you finally learn the mapping)

At any time, `python status.py` tells you where every test stands. You never track
state by memory; you read STATE.md and do the arrow. You never open key.json before
step 9. Those two rules are the entire human discipline.
