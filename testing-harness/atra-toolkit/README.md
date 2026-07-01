# Atramentous Experiment Toolkit

Scripts to run many **blind A/B/C experiments** testing whether embedding intent-memory
in code (Atramentous) helps a later AI agent avoid mistakes. Built and self-tested
following ATRAMENTOUS-TOOLKIT-SPEC.md.

**Status: self-test GREEN.** `python _pipeline/selftest.py` passes all 5 checks
(strip safety incl. code-containing-`[[`, links-only reduction, verify catches drift,
codename blinding + leak-scrub + key round-trip, grader-bundle refuses the key).

## The three arms
- **A (bare):** no annotations — control.
- **B (links-only):** only `[[links]]` survive.
- **C (full):** complete Atramentous web.
Same code in all three; they differ ONLY in annotation. `verify.py` proves that.

## Human operating loop
You never track state in your head. Two rules: **read STATE.md, do the arrow** and
**never open `blind/key.json` until Stage 9.** `python status.py` shows every test's
arrow at once.

```
1.  python new_test.py 007 fastapi <repo_url>        # scaffold + STATE.md
2.  <paste clone_and_clean commands>                  # you run locally (needs creds)
3.  (new chat) LLM writes confounds.json -> you approve, delete dead duplicates
4.  (new TASK-BLIND chat) LLM annotates 00_clean -> drop into arm_C/  (+ provenance)
5.  python strip_links_only.py arm_C arm_B
    python strip_full.py        arm_C arm_A
    python verify.py 00_clean arm_A arm_B arm_C        # STOP if FAIL
6.  (new ANNOTATION-BLIND chat, given ONLY arm_A) propose task pool
    -> you subtract -> freeze task.md
7.  python codename.py arm_A arm_B arm_C blind task.md  # prints codenames only
    -> follow blind/RUN_INSTRUCTIONS.md to launch 9 runs (3/arm) in Cowork/Codex
8.  cp check_TEMPLATE.py check_myexp.py  (fill in the invariant)
    python invariant_test.py runs check_myexp.py        # mechanical primary metric
    python make_grader_bundle.py . grader.zip           # refuses if key.json present
    -> hand grader.zip to a fresh HYPOTHESIS-BLIND chat -> drop scores in grades/
9.  python collate.py .                                  # opens key.json, writes RESULT.md
```
`python status.py` any time → where every test stands.

## The blinding walls (enforced by files, not memory)
- annotator (step 4) is **task-blind** — separate chat, not told the task
- task-picker (step 6) is **annotation-blind** — given only arm_A
- runner (step 7) is **arm-blind** — codenames only, never sees key.json
- grader (step 8) is **hypothesis-blind** — gets runs + rubric, never the key
The two un-leakable walls are yours: assign codenames via the script, don't open the key.

## Scripts
- `new_test.py / state.py / status.py` — scaffolding + the STATE.md dashboard
- `atra_classify.py` — the shared annotation classifier (the load-bearing core)
- `strip_full.py / strip_links_only.py` — derive arm A / arm B
- `verify.py` — THE GATE: arms differ only in annotations; arm A == original
- `manifest.py` — hash/verify trees to catch truncation at every handoff
- `codename.py` — assign codenames, scrub leak files, write key + RUN_INSTRUCTIONS
- `invariant_test.py` + `check_TEMPLATE.py` — mechanical primary metric
- `make_grader_bundle.py` — package for the blind grader, refusing to leak the key
- `collate.py` — the only opener of key.json; writes RESULT.md (raw counts)
- `selftest.py` — proves the toolkit on synthetic data; run before any real use

## Important notes
- Scripts dispatch on their filename; the `*_lib.py` files hold shared logic.
- Cloning is NOT scripted (needs your GitHub creds) — `clone_and_clean` is commands
  you run; everything downstream is scripted.
- Results with ~3 runs/arm are **directional, not statistically powered.** `collate`
  reports raw counts (2/3) and says so. Power comes from running many clean campaigns.
- `state.py --check <test_dir> <stage> <note>` — note the arg order: test_dir first.
- Re-run `selftest.py` after any change to the classifier or strip logic.
