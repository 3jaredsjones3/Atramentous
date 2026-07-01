"""
state scripts: new_test / state / status — keep the human from tracking state by hand.
Run as `python <name>.py ...` (dispatch on argv[0]).
"""
import sys, re
from pathlib import Path
from datetime import datetime, timezone

STAGES = [
    ("S1", "clone & clean", "(-> 00_clean/, manifest)"),
    ("S2", "confounds scanned", "(-> confounds.json, human-approved)"),
    ("S3", "annotated -> arm_C", "(annotator + date in annotation-provenance.md)"),
    ("S4", "arms derived + VERIFIED", "(verify.py must PASS)"),
    ("S5", "task chosen", "(blind-propose 5a, sighted-subtract 5b -> task.md)"),
    ("S6/7", "runs", "(need 3/arm = 9; RUN_INSTRUCTIONS.md drives this)"),
    ("S8", "graded", "(invariant_test.py + blind grader bundle)"),
    ("S9", "unblinded -> RESULT.md", ""),
]
SUBDIRS = ["00_clean", "arm_A", "arm_B", "arm_C", "blind", "runs", "grades"]


def _iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_test(test_id, slug, repo_url, tests_root="."):
    d = Path(tests_root) / f"T{test_id}_{slug}"
    if d.exists():
        sys.exit(f"refusing to overwrite existing {d}")
    for s in SUBDIRS:
        (d / s).mkdir(parents=True)
    lines = [f"# T{test_id} {slug} — STATE", f"repo: {repo_url}", f"created: {_iso()}", ""]
    for sid, label, note in STAGES:
        lines.append(f"[ ] {sid} {label}  {note}".rstrip())
    lines += ["", "## human-judgment log (fill as you go)",
              "- confounds decision:", "- task chosen:", "- anything weird:"]
    (d / "STATE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"created {d}")
    print(f"next: open {d/'STATE.md'} and do the first unchecked line")


def state_check(test_dir, stage_id, note=""):
    f = Path(test_dir) / "STATE.md"
    txt = f.read_text(encoding="utf-8")
    pat = re.compile(rf"^\[ \] ({re.escape(stage_id)}\b.*)$", re.M)
    m = pat.search(txt)
    if not m:
        print(f"(stage {stage_id} not found or already checked)")
        return
    newline = f"[x] {m.group(1)}"
    if note:
        newline += f"  — {note} ({_iso()})"
    txt = txt[:m.start()] + newline + txt[m.end():]
    f.write_text(txt, encoding="utf-8")
    print(f"checked {stage_id}")


def state_show(test_dir):
    print(Path(test_dir).joinpath("STATE.md").read_text(encoding="utf-8"))


def _first_unchecked(state_text):
    for sid, label, _ in STAGES:
        if re.search(rf"^\[ \] {re.escape(sid)}\b", state_text, re.M):
            return sid, label
    return None, "all done"


def _run_progress(test_dir):
    runs = Path(test_dir) / "runs"
    if not runs.exists():
        return 0
    return sum(1 for p in runs.iterdir() if p.is_dir())


def status(tests_root="."):
    root = Path(tests_root)
    tests = sorted([p for p in root.glob("T*") if (p / "STATE.md").exists()])
    if not tests:
        print("no tests found (looked for T*/STATE.md)")
        return
    for t in tests:
        txt = (t / "STATE.md").read_text(encoding="utf-8")
        sid, label = _first_unchecked(txt)
        flag = ""
        if "FAIL" in txt or "BLOCKED" in txt:
            flag = "  !! check STATE (a stage recorded FAIL/BLOCKED)"
        prog = ""
        if sid == "S6/7":
            prog = f"  ({_run_progress(t)}/9 runs)"
        arrow = f"-> {sid} {label}" if sid else "DONE"
        print(f"{t.name:30s} {arrow}{prog}{flag}")


if __name__ == "__main__":
    name = Path(sys.argv[0]).stem
    a = sys.argv[1:]
    if name == "new_test":
        if len(a) < 3:
            sys.exit("usage: python new_test.py <test_id> <slug> <repo_url> [tests_root]")
        new_test(a[0], a[1], a[2], a[3] if len(a) > 3 else ".")
    elif name == "state":
        if a and a[0] == "--check":
            state_check(a[1], a[2], a[3] if len(a) > 3 else "")
        else:
            state_show(a[0])
    elif name == "status":
        status(a[0] if a else ".")
    else:
        sys.exit("run as new_test.py / state.py / status.py")
