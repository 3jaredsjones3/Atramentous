# atra-sweep harness

The skill (`SKILL.md`) is the behavior. These are the wiring options that make it
run on a timer. All of them honor the same contract: **propose, never commit to
main.**

## Files

- `../scripts/atra_lint.py` — the deterministic lint tier (no LLM, read-only).
  Self-contained, stdlib only. Verify it with `python3 atra_lint.py --selftest`.
- `atra-sweep.github-actions.yml` — scheduled CI job that opens a PR (the PR is
  the human gate). Best choice for the propose-never-commit story.
- `atra-sweep.sh` — local cron / launchd / Cowork-schedule harness.

## Recommended layout in a target repo

```
your-repo/
  .atramentous/
    atra_lint.py            # copy of the linter
    atra-sweep.sh           # if running locally
  .github/workflows/
    atra-sweep.yml          # if running in CI (copy of the workflow)
  docs/atramentous/
    register.md             # the memory index (Atramentous core)
    sweeps/                 # digests land here; .state.json tracks the trend
```

## Pick one cadence

- **CI (recommended):** copy the workflow to `.github/workflows/atra-sweep.yml`
  and `atra_lint.py` to `.atramentous/`. It runs nightly and opens a PR only when
  something drifted. Zero secrets needed for the lint tier; add
  `ANTHROPIC_API_KEY` only if you enable the optional judgment pass.
- **Local:** copy `atra-sweep.sh` + `atra_lint.py` to `.atramentous/` and add the
  cron line in the script's header.
- **Cowork:** schedule a task that says "Use atra-sweep on this repo nightly."
  Same skill, Cowork's scheduler instead of cron.

## The boundary, restated

The lint tier is safe to run anywhere, anytime — even on every commit as a
pre-commit or PR check. The judgment tier writes only to a digest and a proposal
branch. Promotion, guardrail edits, and deleting live code stay with
`atra-reconcile` under a human. A scheduled job that commits memory changes to
main unsupervised is exactly the failure mode this design exists to prevent.
