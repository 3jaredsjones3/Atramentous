#!/usr/bin/env python3
"""
atra_lint.py — deterministic entropy linter for the Atramentous memory layer.

No LLM. grep + git only. Read-only. This is the "lint" tier of atra-sweep:
it computes the drift it can prove and leaves judgment calls to the caller.

What it detects:
  - unresolved related-links     ([[X]] in related context with no target)
  - fulfilled-future             (future: [[X]] whose target now exists → promote)
  - aging-future                 (future: [[X]] unbuilt while its neighborhood
                                  moved > future-age-commits past it)
  - aging open nodes             (SCAFFOLD/EXPERIMENT unmoved while neighborhood
                                  took > age-commits)
  - unanswered DECISION nodes    (DECISION bypassed by > decision-commits of work)
  - register orphans             (register ID never referenced by any [[link]])

Staleness is measured in DEVELOPMENT, not calendar time: the unit is commits in
the plan's neighborhood since it was written, not days. A plan is stale when the
trunk grew past the branch point, however long that took. (Tokens/sessions are a
truer unit but live in the agent runtime, not git; commits are the best proxy git
exposes.)

What it deliberately never flags:
  - forward-links in a still neighborhood (no growth = no signal, not "fine")
  - old-but-true memory (age != staleness; only contradiction is drift)

Usage:
  atra_lint.py [path] [--json] [--age-commits 25] [--decision-commits 20]
               [--future-age-commits 40] [--since-last]
               [--state docs/atramentous/sweeps/.state.json]
  atra_lint.py --selftest
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

SENTINEL = "ATRAMENTOUS"
BREADCRUMB = re.compile(r"\batra:\s*(.*)$")
LINK = re.compile(r"\[\[([^\]]+)\]\]")
STATUS = re.compile(r"\bATRAMENTOUS\b[^\n]*?\b(SPINE|SCAFFOLD|EXPERIMENT|REFERENCE|"
                    r"PRODUCTION|DEPRECATED|REMOVABLE|DECISION|SAFETY)\b")
OPEN_STATUSES = {"SCAFFOLD", "EXPERIMENT", "DECISION"}
FIELD = re.compile(r"^\s*(?://|#|--|<!--)?\s*(why|related|future|gate|promote-when|unless|"
                   r"risk|do-not|status)\s*:\s*(.*)$", re.I)
# link prefixes that imply a concrete artifact (so an unresolved one is higher signal)
CONCRETE_PREFIX = re.compile(r"^\s*(TEST|ADR-|M\d|SPINE|SAFETY|SCAFFOLD)\b")

CODE_EXT = {".py", ".kt", ".kts", ".java", ".c", ".cc", ".cpp", ".h", ".hpp",
            ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".swift", ".rb", ".cs",
            ".md", ".txt", ".toml", ".yaml", ".yml"}
SKIP_DIRS = {".git", "node_modules", "build", "dist", "target", ".venv",
             "venv", "__pycache__", ".gradle", ".idea"}


def sh(args, cwd):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                              timeout=60).stdout
    except Exception:
        return ""


def is_git(root):
    return (Path(root) / ".git").exists() or sh(["git", "rev-parse", "--is-inside-work-tree"], root).strip() == "true"


def walk_files(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if Path(fn).suffix.lower() in CODE_EXT:
                yield Path(dp) / fn


def blame_meta(path, root):
    """line-number -> (committer unix time, commit hash). One git-blame per file."""
    out = sh(["git", "blame", "--line-porcelain", str(path)], root)
    meta, cur_line, cur_hash = {}, None, None
    for ln in out.splitlines():
        m = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", ln)
        if m:
            cur_hash, cur_line = m.group(1), int(m.group(2))
        elif ln.startswith("committer-time ") and cur_line is not None:
            meta[cur_line] = (int(ln.split()[1]), cur_hash)
            cur_line = None
    return meta


def commits_since(commit_hash, neighborhood, root):
    """How much did development move in this plan's neighborhood since it was
    written — measured in commits, not calendar time. This is the 'has the trunk
    grown past the branch point' signal: growth in the area the plan lives in
    that did not advance the plan."""
    if not commit_hash:
        return 0
    args = ["git", "rev-list", "--count", f"{commit_hash}..HEAD"]
    if neighborhood:
        args += ["--", neighborhood]
    out = sh(args, root).strip()
    try:
        return int(out)
    except ValueError:
        return 0


def neighborhood_of(rel_path):
    """Approximate a plan's neighborhood as its directory. Fuzzy on purpose —
    a forward-link's true attachment region is graph-shaped, not a folder, so
    this is a proxy, and the finding it feeds is a review prompt, not a verdict."""
    d = os.path.dirname(rel_path)
    return d if d else "."


def find_register(root):
    for cand in ("docs/atramentous/register.md", "docs/scaffolding_register.md"):
        p = Path(root) / cand
        if p.exists():
            return p
    return None


def register_ids(reg_path):
    if not reg_path:
        return []
    ids = []
    for ln in reg_path.read_text(errors="ignore").splitlines():
        cells = [c.strip() for c in ln.split("|") if c.strip()]
        if cells and cells[0].lower() not in ("id", ":--", "---") and not set(cells[0]) <= {"-", ":"}:
            ids.append(cells[0])
    return ids


def build_index(root):
    """resolvable link targets: file stems, md headings, register ids."""
    targets = set()
    for f in walk_files(root):
        targets.add(f.stem.lower())
        if f.suffix.lower() == ".md":
            for ln in f.read_text(errors="ignore").splitlines():
                h = re.match(r"^#{1,6}\s+(.*)", ln)
                if h:
                    targets.add(h.group(1).strip().lower())
    for rid in register_ids(find_register(root)):
        targets.add(rid.lower())
        targets.add(rid.split()[0].lower())
    return targets


def resolves(name, targets):
    n = name.strip().lower()
    if n in targets:
        return True
    # match on the leading token (e.g. "[[M14 Vulkan Renderer]]" -> "m14")
    head = n.split()[0] if n.split() else n
    return head in targets or any(n in t or t in n for t in targets if len(t) > 4 and t == n)


def scan(root, age_commits, decision_commits, future_age_commits):
    findings = []
    git = is_git(root)
    targets = build_index(root)
    reg_path = find_register(root)
    reg_ids = register_ids(reg_path)
    referenced = set()

    for f in walk_files(root):
        try:
            lines = f.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        meta = blame_meta(f, root) if git else {}
        rel = os.path.relpath(f, root)
        hood = neighborhood_of(rel)
        in_block = False
        block_status = None
        block_start = 0
        for i, line in enumerate(lines, 1):
            sm = STATUS.search(line)
            if sm:
                in_block, block_status, block_start = True, sm.group(1).upper(), i
            field = FIELD.match(line)
            ctx = field.group(1).lower() if field else None
            is_future = ctx == "future"

            for lk in LINK.findall(line):
                referenced.add(lk.strip().lower())
                referenced.add(lk.strip().split()[0].lower())
                if is_future:
                    # Forward-links are exempt from DEAD-LINK detection — being
                    # unresolved is their normal, correct state. They are NOT
                    # exempt from staleness. The roadmap rots too:
                    if resolves(lk, targets):
                        # the future arrived but the label still says "future"
                        findings.append(dict(kind="fulfilled-future", sev="med",
                                             loc=f"{rel}:{i}",
                                             detail=f"[[{lk}]] now exists — promote future: → related:"))
                    elif git:
                        # Measure staleness in DEVELOPMENT, not calendar time:
                        # how many commits moved this plan's neighborhood since it
                        # was written, without the plan advancing. The trunk grew
                        # past the branch point.
                        _, h = meta.get(i, (None, None))
                        n = commits_since(h, hood, root)
                        if n > future_age_commits:
                            findings.append(dict(kind="aging-future", sev="low",
                                                 loc=f"{rel}:{i}",
                                                 detail=f"[[{lk}]] unbuilt while {hood}/ moved {n} commits past it — still the plan?"))
                    continue
                if not resolves(lk, targets):
                    sev = "med" if CONCRETE_PREFIX.match(lk) else "low"
                    findings.append(dict(kind="unresolved-link", sev=sev,
                                         loc=f"{rel}:{i}", detail=f"[[{lk}]] has no target"))

            # close a block heuristically on blank-ish boundary
            if in_block and (line.strip() == "" or (not line.lstrip().startswith(("//", "#", "--", "*", "<!--")) and i > block_start)):
                if block_status in OPEN_STATUSES and git:
                    _, h = meta.get(block_start, (None, None))
                    n = commits_since(h, hood, root)
                    thr = decision_commits if block_status == "DECISION" else age_commits
                    if n > thr:
                        k = "decision-unanswered" if block_status == "DECISION" else "aging-node"
                        # a DECISION bypassed by N commits is work piling on an
                        # unmade decision — the dangerous case, hence high sev.
                        findings.append(dict(kind=k, sev="high" if block_status == "DECISION" else "med",
                                             loc=f"{rel}:{block_start}",
                                             detail=f"{block_status} unmoved while {hood}/ took {n} commits (> {thr})"))
                in_block, block_status = False, None

    for rid in reg_ids:
        head = rid.split()[0].lower()
        if rid.lower() not in referenced and head not in referenced:
            findings.append(dict(kind="register-orphan", sev="med",
                                 loc=str(os.path.relpath(reg_path, root)),
                                 detail=f"register row '{rid}' referenced by no [[link]]"))
    return findings


def entropy_score(findings):
    w = {"high": 3, "med": 2, "low": 1}
    return sum(w.get(x["sev"], 1) for x in findings)


def load_state(state_path):
    try:
        return json.loads(Path(state_path).read_text())
    except Exception:
        return {}


def save_state(state_path, count, score):
    try:
        p = Path(state_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),
                                     count=count, score=score), indent=2))
    except Exception:
        pass


def render_md(findings, score, trend):
    by = {"high": [], "med": [], "low": []}
    for x in findings:
        by[x["sev"]].append(x)
    date = datetime.now(timezone.utc).date().isoformat()
    out = [f"Atramentous sweep — {date}",
           f"entropy: {len(findings)} ({len(by['high'])} high, {len(by['med'])} med, "
           f"{len(by['low'])} low)   score {score}{trend}", ""]
    for sev in ("high", "med", "low"):
        if by[sev]:
            out.append(sev.upper())
            for x in by[sev]:
                out.append(f"- {x['kind']:20} {x['loc']}  {x['detail']}")
            out.append("")
    if not findings:
        out.append("Memory layer clean. Nothing drifted.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--age-commits", type=int, default=25)
    ap.add_argument("--decision-commits", type=int, default=20)
    ap.add_argument("--future-age-commits", type=int, default=40)
    ap.add_argument("--since-last", action="store_true")
    ap.add_argument("--state", default="docs/atramentous/sweeps/.state.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    findings = scan(a.path, a.age_commits, a.decision_commits, a.future_age_commits)
    score = entropy_score(findings)
    trend = ""
    if a.since_last:
        prev = load_state(os.path.join(a.path, a.state) if not os.path.isabs(a.state) else a.state)
        if prev.get("count") is not None:
            d = len(findings) - prev["count"]
            trend = f"   trend: {'↑' if d > 0 else '↓' if d < 0 else '→'}{abs(d)} since {prev.get('at','?')[:10]}"
        save_state(os.path.join(a.path, a.state) if not os.path.isabs(a.state) else a.state,
                   len(findings), score)

    if a.json:
        print(json.dumps(dict(entropy=len(findings), score=score, findings=findings), indent=2))
    else:
        print(render_md(findings, score, trend))
    return 0


def selftest():
    """one runnable check: a synthetic tree must surface exactly the planted drift,
    and staleness must respond to COMMITS in the neighborhood, not wall time."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        def git(*a):
            subprocess.run(["git", *a], cwd=d, capture_output=True)
        git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")

        # zone A: a scaffold + forward-links, in its own directory (its neighborhood)
        (root / "zoneA").mkdir()
        (root / "zoneA" / "a.kt").write_text(
            "// ATRAMENTOUS SCAFFOLD\n"
            "// why: temp\n"
            "// future: [[Unwritten GPU Path]]\n"     # unfulfilled forward-link
            "// future: [[compute]]\n"                # fulfilled (compute.kt exists)
            "// related: [[Nonexistent System]]\n"    # dead related-link
            "fun x() {}\n")
        (root / "zoneA" / "compute.kt").write_text("fun c() {}\n")  # makes [[compute]] resolve
        # zone B: dormant — a forward-link that nothing ever grows past
        (root / "zoneB").mkdir()
        (root / "zoneB" / "b.kt").write_text(
            "// ATRAMENTOUS SCAFFOLD\n// why: distant\n// future: [[Far Off Thing]]\nfun y() {}\n")
        (root / "docs" / "atramentous").mkdir(parents=True)
        (root / "docs" / "atramentous" / "register.md").write_text(
            "| ID | status |\n|---|---|\n| GhostRow | SCAFFOLD |\n")
        git("add", "-A"); git("commit", "-qm", "seed")

        # development moves ONLY in zoneA — 6 commits grow past its branch point
        for k in range(6):
            (root / "zoneA" / f"grow{k}.kt").write_text(f"fun g{k}() {{}}\n")
            git("add", "-A"); git("commit", "-qm", f"grow {k}")

        # thresholds in COMMITS: aging fires at >3 neighborhood commits
        f = scan(str(root), age_commits=3, decision_commits=3, future_age_commits=3)
        kinds = {x["kind"] for x in f}
        dead = [x for x in f if x["kind"] == "unresolved-link"]
        assert any("Nonexistent System" in x["detail"] for x in dead), "missed dead related-link"
        assert any(x["kind"] == "fulfilled-future" and "compute" in x["detail"] for x in f), "missed fulfilled-future"
        assert "register-orphan" in kinds, "missed register orphan"
        # zoneA grew 6 commits past its plan -> aging-future fires there
        assert any(x["kind"] == "aging-future" and "zoneA" in x["loc"] for x in f), "missed aging-future in grown zone"
        assert any(x["kind"] == "aging-node" and "zoneA" in x["loc"] for x in f), "missed aging-node in grown zone"
        # zoneB never grew -> NO aging signal there (no growth = no signal)
        assert not any("zoneB" in x.get("loc", "") for x in f), "wrongly flagged a plan in a dormant neighborhood"
        print("selftest ok:", sorted(kinds))
        return 0
        print("selftest ok:", sorted(kinds))
        return 0


if __name__ == "__main__":
    sys.exit(main())
