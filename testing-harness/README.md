# Testing Harness

Source-first, diffable home for Atramentous's experiment protocol, toolkit, and
experiment records. Everything here is plain text so it diffs and reviews like
code — no zips checked in.

## Layout

- `protocol.md` — the clean-room experiment protocol: how a blind evaluation run
  is set up and executed.
- `toolkit-spec.md` — the design/spec for the local harness toolkit (what each
  pipeline stage is responsible for).
- `atra-toolkit/` — the local harness scripts (`_pipeline/`) that implement the
  toolkit spec: classification, stripping, manifesting, grading, self-test.
- `cartridge/` — the external submission format: `CARTRIDGE-FORMAT.md` and
  `SUBMISSION-SCHEMA.md` define what a third party submits for evaluation.
- `records/m1/` — records from the first (M1) experiment run: the evidence
  gate, the experiment record itself, and grammar provenance notes.
- `transcripts/` — historical discussion and provenance transcripts kept for
  context on how the harness and protocol were arrived at.

## Conventions

- Generated output (`_selftest_work/`, `__pycache__/`, `*.pyc`) is never
  committed — see `.gitignore`.
- Prefer Markdown/text source over archives. If material arrives as a zip,
  unpack it into the matching folder above and drop the zip.
