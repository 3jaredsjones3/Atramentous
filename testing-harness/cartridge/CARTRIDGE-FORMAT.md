# Atramentous Test Cartridge — format spec

A cartridge is a SEALED, pre-built test that a stranger can run with zero judgment
calls. All the leak-prone, judgment-heavy work (annotation, task selection, invariant
definition, arm derivation + verification, blinding) is done by YOU before sealing.
The tester only RUNS it and submits artifacts. This makes crowd results comparable
(everyone ran the same task) and trustable (you re-verify the artifacts).

## Cartridge contents
```
cartridge_<id>/
  venus/  saturn/  earth/      # the 3 arms, ALREADY CODENAMED (no arm_A/B/C names)
  manifest_arms.json           # sha256 of every file in each codenamed arm
  task.md                      # the frozen task paragraph (identical for all arms)
  check.py                     # the mechanical invariant test (your authored predicate)
  comprehension_prompt.txt     # exact pre-task question the runner must answer
  RUN.md                       # codename-only run instructions
  cartridge.json               # {id, author, repo_source, commit, n_per_arm, created}
```
**NO key.json in the cartridge.** The codename->arm key lives ONLY in your private
records, indexed by cartridge id. The tester runs blind and CANNOT unblind, because the
key was never shipped. You rejoin the key when aggregating. Blinding is enforced by the
key's ABSENCE, not the tester's discipline.

## How YOU build a cartridge (using the toolkit)
1. Acquire + clean the repo (Stage 1), scan confounds (Stage 2), remove dead duplicates.
2. Annotate -> arm_C (Stage 3, task-blind).
3. Pick the task (Stage 5: blind-propose, sighted-subtract), freeze task.md.
4. Derive arm_B, arm_A; run verify.py — MUST pass (Stage 4).
5. Write check.py from check_TEMPLATE.py — the mechanical PRESERVED/BROKEN predicate
   for THIS task's hidden invariant. Test it on a hand-made broken + good file.
6. codename.py -> venus/saturn/earth + key.json. MOVE key.json out of the cartridge
   into your private records/keys/<id>.json. Run manifest.py on each codenamed arm ->
   manifest_arms.json.
7. Write RUN.md + cartridge.json. Zip. That's a sealed cartridge.

## What RUN.md tells the tester (codename-only, no judgment)
For EACH codename (venus, saturn, earth), do N runs (N = cartridge.json.n_per_arm):
1. BEFORE editing code, paste comprehension_prompt.txt to the agent; save its answer
   verbatim as comprehension.txt in the run folder.
2. Give the agent that codename's repo + task.md. Let it complete the task.
3. Save the modified repo to runs/<codename>_run<n>/ (including comprehension.txt).
After all runs: `python check.py runs/` -> writes mechanical.csv. Then bundle (see
SUBMISSION-SCHEMA.md) and submit. The tester picks NOTHING, judges NOTHING, writes no
invariant — it was all sealed.

## Why the tester does the comprehension capture
It is the only evidence of what the RUNNING agent understood (vs. the annotations it
inherited). It is what separates not-noticing / not-binding / not-generalizing. Without
it a cartridge run is half-blind. RUN.md makes it step 1, mandatory.

## check.py contract
Same as check_TEMPLATE.py: `check_run(run_dir) -> "preserved"|"broken"|"engaged-no"`.
It reads the relevant file(s) and decides mechanically. No model. The author (you)
writes it knowing the hidden invariant; the tester just runs it; YOU re-run it on the
submitted repos during validation so a faked CSV can't pass.

## Cartridge id convention
`<repo-slug>_<task-slug>_v<n>` e.g. `fastapi_depinject_v1`. Bump v if you change the
task or annotations — results are only comparable within the same cartridge version.
