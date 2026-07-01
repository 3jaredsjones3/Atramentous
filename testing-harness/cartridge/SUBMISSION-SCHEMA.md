# Atramentous Cartridge Submission — schema + validator

The point: accept crowd results you did NOT supervise, and trust them anyway, because
the submission ships the PROOF it was run correctly and you RE-VERIFY the artifacts
rather than trusting the tester's word. Trust artifacts, not testers.

## What a valid submission contains
```
submission_<cartridge_id>_<tester>/
  meta.json          # {cartridge_id, tester_handle, model, thinking: true|false, date}
  arm_manifests.json # sha256 of the arms AS THE TESTER RECEIVED THEM (each codename)
  mechanical.csv     # check.py output: codename,run,engaged,preserved
  comprehension/     # <codename>_run<n>.txt — verbatim pre-task answers, one per run
  runs/              # <codename>_run<n>/ — the actual modified repos
```
`runs/` is required because YOU re-run check.py on them; the tester's mechanical.csv is
cross-checked, never trusted on its own.

## The validator (a script you run / CI runs on each PR)
Reject the submission unless ALL pass:

1. **Arms were the real, unmodified arms.** `arm_manifests.json` must equal the
   cartridge's `manifest_arms.json` for that cartridge_id. (Proves they ran YOUR arms,
   not edited ones — and that arm_B/A weren't secretly given annotations, etc.)
2. **The mechanical verdicts are real.** Re-run the sealed `check.py` against the
   submitted `runs/` yourself. The verdicts you get MUST match the submitted
   mechanical.csv. (A faked CSV fails here — the repos decide, not the tester.)
3. **Completeness.** Exactly N runs per codename (N from cartridge.json), each with a
   comprehension file. Missing comprehension or wrong run count -> reject.
4. **Engagement sanity.** If EVERY run is engaged-no, flag for manual review (the
   tester may have mis-run it — agents that touched nothing trivially "preserve").
5. **meta.json well-formed.** model + thinking present (needed for the gradient).

On pass: append rows to the aggregate table, keyed by
`(cartridge_id, model, thinking, arm)` — rejoining the codename->arm key from your
private records/keys/<id>.json. The tester never had the key; you add it now.

## Aggregate table (one growing CSV, the whole payoff)
Columns: cartridge_id, model, thinking, arm, engaged, preserved, tester, date, run_id.
From this you compute, per cartridge AND pooled:
- per-arm preserved-rate among engaged runs (the primary metric)
- (B-A) and (C-B) gaps
- the SAME broken down by model + thinking -> the capability gradient
Per-cartridge accumulation across many testers is what crosses n=3 into real power.

## The upload point (keep it dead simple)
A public GitHub repo. Tester zips the submission, opens a PR adding it under
`submissions/`. CI runs the validator; green check = mergeable; you merge = accepted.
No web app, no DB, no auth. The validator script is the only real code. The "where" is
just a repo with PR review.

## Comprehension grading (separate, blinded, async)
The comprehension answers still need scoring (did the agent grasp the relevant
constraint). Do this in BATCHES, blinded: periodically collect accepted submissions'
comprehension files, strip tester+codename+model labels, shuffle, score against a fixed
per-cartridge rubric in a fresh chat, rejoin labels after. Same blind-grading
discipline as M1 — just batched across many submissions for efficiency. This is the one
step that isn't fully mechanical; everything else the validator does for free.

## Anti-gaming notes (since it's public)
- You re-run check.py, so verdicts can't be faked — only real repos count.
- Manifests must match, so testers can't hand-edit arms to favor an outcome.
- The key is never shipped, so testers can't even tell which arm they're helping.
- A tester COULD submit low-effort agent runs (a weak model, no real attempt). That's
  fine — it's still a real data point at that capability level; meta.json records the
  model so you can filter/group. Garbage-in is bounded because the conditions are
  recorded, not hidden.
