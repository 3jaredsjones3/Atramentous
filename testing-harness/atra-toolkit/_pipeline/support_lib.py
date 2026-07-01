"""
support scripts: manifest / codename / make_grader_bundle / collate.
Run each as `python <name>.py ...` (dispatch on argv[0]).
"""
import sys, json, hashlib, shutil, random
from pathlib import Path

SKIP = {".git", "node_modules"}


def _files(root):
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and not any(s in p.parts for s in SKIP):
            yield p


# ---------------- manifest ----------------
def manifest_write(root):
    root = Path(root)
    lines = []
    for p in _files(root):
        if p.name == "manifest.sha256":
            continue  # never hash the manifest into itself
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{str(p.relative_to(root)).replace(chr(92),'/')}  {h}")
    (root / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"manifest: {len(lines)} files")


def manifest_verify(root, manifest_file):
    root = Path(root)
    want = {}
    for ln in Path(manifest_file).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            rel, h = ln.rsplit("  ", 1); want[rel] = h
    have = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in _files(root) if p.name != "manifest.sha256"}
    bad = []
    for rel in sorted(set(want) | set(have)):
        if rel not in have: bad.append(f"MISSING {rel}")
        elif rel not in want: bad.append(f"ADDED {rel}")
        elif want[rel] != have[rel]: bad.append(f"CHANGED {rel}")
    if bad:
        print("MANIFEST FAIL:"); [print("  -", b) for b in bad[:50]]; sys.exit(1)
    print("MANIFEST PASS")


# ---------------- codename (the blinding step) ----------------
# Exact experiment-generated filenames that may carry arm identity. We remove ONLY
# these exact names (case-insensitive) — never fuzzy substrings of arbitrary repo
# docs, which could delete legitimate files like a repo's own ANALYSIS.md.
LEAK_EXACT = {
    "annotation-provenance.md", "changes_summary.md", "changes.md",
    "refactoring_summary.md", "refactoring_notes.md", "executive_summary.txt",
    "executive_summary.md", "quick_start.md", "code_changes.md",
    "before_after_comparison.md", "activepath_robustness.md", "analysis.md",
    "readme_atra.md",
}


def _scrub_leaks(dirpath):
    """Delete experiment-generated report files whose names could reveal the arm.
    EXACT-name match only (case-insensitive). The right long-term fix is to never
    write report files into the arm dirs at all — keep experiment metadata BESIDE the
    arms — but this guards against the common agent habit of dropping SUMMARY files in."""
    removed = []
    for p in list(_files(dirpath)):
        if p.name.lower() in LEAK_EXACT:
            p.unlink(); removed.append(p.name)
    return removed


def codename(arm_a, arm_b, arm_c, blind_dir, task_file, pool=None):
    blind_dir = Path(blind_dir); blind_dir.mkdir(parents=True, exist_ok=True)
    pool = pool or ["venus", "saturn", "earth", "titan", "rhea", "mimas", "dione", "iapetus"]
    names = random.sample(pool, 3)
    mapping = dict(zip(names, ["A", "B", "C"]))
    arms = {"A": Path(arm_a), "B": Path(arm_b), "C": Path(arm_c)}
    for name, arm in mapping.items():
        dst = blind_dir / name
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(arms[arm], dst, ignore=shutil.ignore_patterns(*SKIP))
        _scrub_leaks(dst)
    (blind_dir / "key.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    task = Path(task_file).read_text(encoding="utf-8") if Path(task_file).exists() else "(task.md not found)"
    instr = ("# RUN INSTRUCTIONS (codenames only — do not infer anything from them)\n\n"
             f"Codenames this test: {', '.join(names)}\n\n"
             "For EACH codename, do 3 runs. For each run:\n"
             "1. BEFORE editing any code, answer in your own words and save as "
             "comprehension.txt: 'What is this project, what are its load-bearing "
             "constraints, and what are you unsure about?'\n"
             "2. Then perform the task below on that codename's copy.\n"
             "3. Save the modified repo to runs/<codename>_run<n>/ (with comprehension.txt).\n\n"
             "## TASK\n" + task + "\n")
    (blind_dir / "RUN_INSTRUCTIONS.md").write_text(instr, encoding="utf-8")
    # print ONLY codenames, never the mapping
    print("codenames:", ", ".join(names))
    print("(key.json written — DO NOT open until grading is complete)")


# ---------------- grader bundle (refuses to leak the key) ----------------
def make_grader_bundle(test_dir, out_zip):
    test_dir = Path(test_dir)
    import zipfile, tempfile
    from strip_lib import strip_full
    # HARD GUARD first: never include any key.json
    runs = test_dir / "runs"
    src_files = list(_files(runs)) if runs.exists() else []
    if any(p.name == "key.json" for p in src_files):
        sys.exit("REFUSED: a key.json is present under runs/ — would leak the mapping")
    # SANITIZE: strip annotations from each run's repo so a model grader can't infer
    # the arm from the presence of ATRAMENTOUS blocks (arm C) or bare links (arm B).
    # The mechanical invariant test runs on the UNsanitized runs/ separately; this
    # sanitized copy is only for the hypothesis-blind model/human grader. Comprehension
    # files are kept separate (they may mention annotations by nature) and NOT bundled
    # here — grade them in their own blinded batch.
    tmp = Path(tempfile.mkdtemp())
    sanitized = tmp / "runs"
    for run_dir in sorted([d for d in runs.iterdir() if d.is_dir()]) if runs.exists() else []:
        strip_full(run_dir, sanitized / run_dir.name)
        # drop any comprehension.txt from the grader copy (kept for separate grading)
        for c in (sanitized / run_dir.name).rglob("comprehension*.txt"):
            c.unlink()
    include = list(_files(sanitized))
    extra = [test_dir / f for f in ("task.md", "rubric.md") if (test_dir / f).exists()]
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in include:
            z.write(p, p.relative_to(tmp))
        for p in extra:
            z.write(p, p.name)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"grader bundle: {out_zip} ({len(include)} sanitized run files + "
          f"{len(extra)} docs; annotations stripped, key & comprehension excluded)")


# ---------------- collate (the only opener of key.json) ----------------
def collate(test_dir):
    test_dir = Path(test_dir)
    key = json.loads((test_dir / "blind" / "key.json").read_text(encoding="utf-8"))
    cn2arm = key  # {codename: arm}
    mech = test_dir / "grades" / "mechanical.csv"
    rows = []
    if mech.exists():
        for ln in mech.read_text(encoding="utf-8").splitlines()[1:]:
            if ln.strip(): rows.append(ln.split(","))
    # rows: codename,run,engaged,preserved
    by_arm = {"A": [], "B": [], "C": []}
    for r in rows:
        cn = r[0]
        arm = cn2arm.get(cn) or cn2arm.get(cn.split("_")[0])
        if arm: by_arm[arm].append(r)

    def rate(arm):
        eng = [r for r in by_arm[arm] if r[2].strip().lower() in ("yes", "true", "1")]
        pres = [r for r in eng if r[3].strip().lower() in ("preserved", "yes", "true")]
        return len(pres), len(eng)

    out = ["# RESULT\n", f"arm A = control(bare), B = links-only, C = full\n",
           "(raw counts; DIRECTIONAL not statistically powered)\n"]
    for arm in ("A", "B", "C"):
        p, n = rate(arm)
        out.append(f"- arm {arm}: preserved {p}/{n} engaged runs")
    pa, na = rate("A"); pb, nb = rate("B"); pc, nc = rate("C")
    out.append("")
    out.append(f"gap (B-A): {(pb/nb if nb else 0)-(pa/na if na else 0):+.2f} (links vs bare)")
    out.append(f"gap (C-B): {(pc/nc if nc else 0)-(pb/nb if nb else 0):+.2f} (full vs links)")
    (test_dir / "RESULT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    print("\nwrote RESULT.md")


if __name__ == "__main__":
    name = Path(sys.argv[0]).stem
    a = sys.argv[1:]
    if name == "manifest":
        if len(a) >= 3 and a[1] == "--verify": manifest_verify(a[0], a[2])
        else: manifest_write(a[0])
    elif name == "codename":
        codename(a[0], a[1], a[2], a[3], a[4])
    elif name == "make_grader_bundle":
        make_grader_bundle(a[0], a[1])
    elif name == "collate":
        collate(a[0])
    else:
        sys.exit("run as manifest.py / codename.py / make_grader_bundle.py / collate.py")
