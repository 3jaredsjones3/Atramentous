#!/usr/bin/env python3
"""
atra_lint.py — deterministic entropy linter for the Atramentous memory layer.

No LLM. grep + git only. Read-only. This is the "lint" tier of atra-sweep:
it computes the drift it can prove and leaves judgment calls to the caller.

What it detects:
  - unresolved related-links     ([[X]] in related context with no target;
                                  includes dead [[store:<slug>]] pointers)
  - fulfilled-future             (future: [[X]] whose target now exists → promote)
  - aging-future                 (future: [[X]] unbuilt while its neighborhood
                                  moved > future-age-commits past it)
  - aging open nodes             (SCAFFOLD/EXPERIMENT unmoved while neighborhood
                                  took > age-commits)
  - unanswered DECISION nodes    (DECISION bypassed by > decision-commits of work)
  - register orphans             (register ID never referenced by any [[link]])
  - over-density                 (a file or function carrying more ASSISTIVE
                                  annotation than its budget → promote lowest-value
                                  nodes to the external store)
  - should-externalize           (a heavy inline ASSISTIVE node whose region has
                                  grown > externalize-threshold neighborhood-commits
                                  → move its payload to the store, leave a pointer)
  - consult-gateless             (a CONSULT node — a decision deferred to a human —
                                  whose gate names no [[phase]]; "later means never")

Staleness is measured in DEVELOPMENT, not calendar time: the unit is commits in
the plan's neighborhood since it was written, not days. A plan is stale when the
trunk grew past the branch point, however long that took. (Tokens/sessions are a
truer unit but live in the agent runtime, not git; commits are the best proxy git
exposes.)

The density and growth tiers govern ASSISTIVE memory only. A GUARDRAIL — a node
whose status is SAFETY or SPINE, or that carries a `do-not:` field — is never
budget-counted and never externalized: safety memory stays inline and always
visible regardless of density or growth.

Every magnitude below is a CLI flag whose default is a *reasoned default — tune
with use, not empirically derived* (see --help).

What it deliberately never flags:
  - forward-links in a still neighborhood (no growth = no signal, not "fine")
  - old-but-true memory (age != staleness; only contradiction is drift)
  - memory inside small / young / dormant regions (the inline tier is correct there)

Usage:
  atra_lint.py [path] [--json] [--age-commits 25] [--decision-commits 20]
               [--future-age-commits 40] [--max-nodes-per-function 1]
               [--node-line-ratio 25] [--density-floor 1]
               [--externalize-threshold 40] [--heavy-node-lines 4]
               [--since-last] [--state docs/atramentous/sweeps/.state.json]
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
                    r"PRODUCTION|DEPRECATED|REMOVABLE|DECISION|SAFETY|CONSULT)\b")
OPEN_STATUSES = {"SCAFFOLD", "EXPERIMENT", "DECISION"}
FIELD = re.compile(r"^\s*(?://|#|--|<!--)?\s*(why|related|future|gate|promote-when|unless|"
                   r"risk|do-not|status|default|ask)\s*:\s*(.*)$", re.I)
# link prefixes that imply a concrete artifact (so an unresolved one is higher signal)
CONCRETE_PREFIX = re.compile(r"^\s*(TEST|ADR-|M\d|SPINE|SAFETY|SCAFFOLD)\b")
# externalization pointer: `[[store:<slug>]]` points at docs/atramentous/store/<slug>.md
STORE_LINK = re.compile(r"^\s*store:(.+)$", re.I)
# function-header heuristic (keyword forms across langs). A node is attributed to
# the function header that immediately FOLLOWS it (annotations sit above their
# code); nodes below the last header attach to it. Deliberately a proxy — it feeds
# a review prompt, not a verdict, exactly like neighborhood_of(). Brace-only
# headers (C/Java `int f(){`) are intentionally NOT matched, to avoid colliding
# with control-flow (`if (...) {`); those files are governed by the file ratio.
FUNC_DEF = re.compile(r"^\s*(?:[\w@$<>\[\].]+\s+)*(?:def|fn|fun|func|function)\b")

CODE_EXT = {".py", ".kt", ".kts", ".java", ".c", ".cc", ".cpp", ".h", ".hpp",
            ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".swift", ".rb", ".cs",
            ".md", ".txt", ".toml", ".yaml", ".yml"}
SKIP_DIRS = {".git", "node_modules", "build", "dist", "target", ".venv",
             "venv", "__pycache__", ".gradle", ".idea"}


def sh(args, cwd):
    try:
        # decode as utf-8 explicitly: the default locale codec (cp1252 on Windows)
        # chokes on non-ASCII in git output / annotations (e.g. em-dashes).
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60).stdout
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
    """resolvable link targets: file stems, md headings, register ids, store slugs."""
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
    # externalized-memory store: each note is one file, its stem is its slug/id.
    # `[[store:<slug>]]` resolves iff docs/atramentous/store/<slug>.md exists, so a
    # pointer to a missing note is a dead link like any other.
    store_dir = Path(root) / "docs" / "atramentous" / "store"
    if store_dir.is_dir():
        for sf in store_dir.glob("*.md"):
            targets.add(f"store:{sf.stem.lower()}")
    return targets


def resolves(name, targets):
    n = name.strip().lower()
    if n in targets:
        return True
    # match on the leading token (e.g. "[[M14 Vulkan Renderer]]" -> "m14")
    head = n.split()[0] if n.split() else n
    return head in targets or any(n in t or t in n for t in targets if len(t) > 4 and t == n)


def block_label(status, block_lines):
    """short human handle for a heavy node: status + its first link, else status."""
    for ln in block_lines:
        m = LINK.search(ln)
        if m:
            return f"{status} [[{m.group(1).strip()}]]"
    return status


def breadcrumb_label(text):
    m = LINK.search(text)
    if m:
        return f"[[{m.group(1).strip()}]]"
    return ("atra: " + text.strip())[:48]


def extract_nodes(lines):
    """Re-parse a file into discrete memory nodes for the density/growth tiers.
    Read-only and independent of the aging loop, so it adds detection without
    perturbing any existing finding. Each node records whether it is a GUARDRAIL
    (status SAFETY/SPINE, or carries a do-not: field) — guardrails are never
    budget-counted and never externalized."""
    nodes, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        sm = STATUS.search(line)
        if sm:
            status = sm.group(1).upper()
            fields, j, gate_link = set(), i + 1, False
            while j < n:
                lj = lines[j]
                fm = FIELD.match(lj)
                if fm:
                    name = fm.group(1).lower()
                    fields.add(name)
                    # a gate to a NAMED phase carries a [[link]]; "gate: later" doesn't.
                    if name == "gate" and "[[" in lj:
                        gate_link = True
                    j += 1; continue
                if lj.strip() == "":
                    break
                if lj.lstrip().startswith(("//", "#", "--", "*", "<!--")):
                    j += 1; continue
                break
            guard = status in ("SAFETY", "SPINE") or "do-not" in fields
            nodes.append(dict(start=i + 1, kind="block", status=status, fields=fields,
                              guard=guard, pointer=False, nlines=j - i, gate_link=gate_link,
                              label=block_label(status, lines[i:j])))
            i = j; continue
        bm = BREADCRUMB.search(line)
        if bm:
            pointer = "[[store:" in line.lower()
            nodes.append(dict(start=i + 1, kind="breadcrumb", status=None, fields=set(),
                              guard=False, pointer=pointer, nlines=1,
                              label=breadcrumb_label(bm.group(1))))
        i += 1
    return nodes


def value_score(nd):
    """Deterministic 'keep-inline value' — HIGHER means more valuable, so the
    LOWEST-scoring assistive nodes are promoted to the store first. Active roadmap
    and open lifecycle outrank a bare related-link breadcrumb."""
    s = 0
    f = nd["fields"]
    if "future" in f or "gate" in f:
        s += 4
    if nd["status"] in ("SCAFFOLD", "EXPERIMENT", "DECISION"):
        s += 3
    if "risk" in f:
        s += 2
    if "why" in f:
        s += 1
    return s


def promote_suggestion(candidates, over):
    """Name the lowest-value externalizable nodes to move. Deterministic order:
    value asc, then heaviest (most lines) first for biggest density relief, then
    line order. Guardrails and existing pointers are excluded by the caller."""
    ranked = sorted(candidates, key=lambda nd: (value_score(nd), -nd["nlines"], nd["start"]))
    if not ranked:
        return "consolidate pointers (no externalizable node left — payload is already guardrails/pointers)"
    head = ranked[0]
    extra = f" (+{over - 1} more)" if over > 1 else ""
    return f"promote lowest-value to store: {head['label']} @L{head['start']}{extra}"


def density_findings(rel, lines, nodes, max_per_func, node_line_ratio, density_floor):
    """over-density: a function or file carrying more ASSISTIVE annotation than its
    budget. Guardrails are never counted (the density rule governs assistive memory
    only); pointers ARE counted (a wall of summons is the noise the cap kills)."""
    out = []
    assistive = [nd for nd in nodes if not nd["guard"]]

    # --- per-function budget (node COUNT) ---
    headers = [i + 1 for i, l in enumerate(lines) if FUNC_DEF.match(l)]
    if headers:
        buckets = {h: [] for h in headers}
        for nd in assistive:
            # attribute to the header immediately at/after the node; else the last
            following = [h for h in headers if h >= nd["start"]]
            buckets[following[0] if following else headers[-1]].append(nd)
        for h in headers:
            here = buckets[h]
            if len(here) > max_per_func:
                over = len(here) - max_per_func
                cand = [nd for nd in here if not nd["pointer"]]
                out.append(dict(kind="over-density", sev="low", loc=f"{rel}:{h}",
                                detail=f"{len(here)} assistive nodes on one function "
                                       f"(> {max_per_func}) — {promote_suggestion(cand, over)}"))

    # --- file budget (node-LINE : code-LINE ratio) ---
    nonblank = sum(1 for l in lines if l.strip())
    mem_all = sum(nd["nlines"] for nd in nodes)
    counted = sum(nd["nlines"] for nd in assistive)
    code_lines = max(0, nonblank - mem_all)
    # the 1:N ratio is only meaningful once a file has at least N code lines; below
    # that, density is governed by the per-function cap alone (keeps tiny scaffolds
    # from tripping a ratio that can't yet say anything).
    if code_lines >= node_line_ratio:
        budget = max(density_floor, code_lines // node_line_ratio)
        if counted > budget:
            over = counted - budget
            cand = [nd for nd in assistive if not nd["pointer"]]
            out.append(dict(kind="over-density", sev="low", loc=rel,
                            detail=f"{counted} assistive node-lines vs {code_lines} code "
                                   f"(budget {budget}) — {promote_suggestion(cand, over)}"))
    return out


def externalize_findings(rel, hood, nodes, meta, root, threshold, heavy_lines):
    """should-externalize: a HEAVY inline assistive node whose region has grown past
    --externalize-threshold neighborhood-commits → move its payload to the store and
    leave a pointer. Small/young/dormant regions keep memory inline (no growth, no
    flag). Guardrails are never externalized regardless of growth."""
    out = []
    for nd in nodes:
        if nd["kind"] != "block" or nd["guard"] or nd["nlines"] < heavy_lines:
            continue
        _, h = meta.get(nd["start"], (None, None))
        n = commits_since(h, hood, root)
        if n > threshold:
            out.append(dict(kind="should-externalize", sev="low", loc=f"{rel}:{nd['start']}",
                            detail=f"{nd['label']} heavy inline while {hood}/ grew {n} commits "
                                   f"(> {threshold}) — move payload to store, leave a pointer"))
    return out


def collab_findings(rel, nodes):
    """consult-gateless: a CONSULT node (a decision deferred to a human) whose gate
    does not name a phase with a [[link]]. A deferred consultation without a gate to
    a NAMED phase is the 'later means never' failure — it decides by neglect. This is
    the forward-link honesty rule applied to decisions: structural, deterministic.
    Guardrails are exempt (a CONSULT carrying do-not is never budgeted/gated here)."""
    out = []
    for nd in nodes:
        if nd.get("status") == "CONSULT" and not nd["guard"]:
            if "gate" not in nd["fields"] or not nd.get("gate_link"):
                out.append(dict(kind="consult-gateless", sev="med", loc=f"{rel}:{nd['start']}",
                                detail="CONSULT has no gate to a [[named phase]] — gate it to "
                                       "the phase where it ripens, or it decides by neglect"))
    return out


def scan(root, age_commits, decision_commits, future_age_commits,
         max_per_func=1, node_line_ratio=25, density_floor=1,
         externalize_threshold=40, heavy_node_lines=4):
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

        # density + growth tiers (additive; independent of the aging loop above)
        nodes = extract_nodes(lines)
        findings += density_findings(rel, lines, nodes, max_per_func,
                                     node_line_ratio, density_floor)
        findings += collab_findings(rel, nodes)   # structural, git-independent
        if git:
            findings += externalize_findings(rel, hood, nodes, meta, root,
                                             externalize_threshold, heavy_node_lines)

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
    # density + externalization budgets. Every magnitude below is a reasoned
    # default — tune with use, not empirically derived.
    ap.add_argument("--max-nodes-per-function", type=int, default=1,
                    help="max assistive memory nodes on one function before over-density "
                         "(reasoned default 1; guardrails never counted)")
    ap.add_argument("--node-line-ratio", type=int, default=25,
                    help="allowed code lines per assistive node-line; file over-density "
                         "fires above this (reasoned default 25 ~ 1 node-line / 25 code)")
    ap.add_argument("--density-floor", type=int, default=1,
                    help="free assistive node-lines every file gets before the ratio "
                         "applies (reasoned default 1)")
    ap.add_argument("--externalize-threshold", type=int, default=40,
                    help="neighborhood-commits of growth past a heavy inline node before "
                         "should-externalize fires (reasoned default 40, deliberately high)")
    ap.add_argument("--heavy-node-lines", type=int, default=4,
                    help="min lines for a block to count as 'heavy' / externalizable "
                         "(reasoned default 4)")
    ap.add_argument("--since-last", action="store_true")
    ap.add_argument("--state", default="docs/atramentous/sweeps/.state.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    findings = scan(a.path, a.age_commits, a.decision_commits, a.future_age_commits,
                    max_per_func=a.max_nodes_per_function, node_line_ratio=a.node_line_ratio,
                    density_floor=a.density_floor, externalize_threshold=a.externalize_threshold,
                    heavy_node_lines=a.heavy_node_lines)
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
        # a GUARDRAIL inside the SAME grown neighborhood — must NEVER be externalized
        (root / "zoneA" / "safety.kt").write_text(
            "// ATRAMENTOUS SAFETY\n"
            "// why: atomic save protects against data loss on crash\n"
            "// do-not: write in place; always temp-then-rename\n"
            "// invariant: fsync the temp file before the rename\n"
            "fun atomicSave() {}\n")
        # zone B: dormant — a forward-link that nothing ever grows past
        (root / "zoneB").mkdir()
        (root / "zoneB" / "b.kt").write_text(
            "// ATRAMENTOUS SCAFFOLD\n// why: distant\n// future: [[Far Off Thing]]\nfun y() {}\n")
        # a dormant zone with a HEAVY assistive node — heaviness alone must NOT
        # externalize; only growth does (this zone never grows)
        (root / "zoneDorm").mkdir()
        (root / "zoneDorm" / "dh.kt").write_text(
            "// ATRAMENTOUS SCAFFOLD\n"
            "// why: a heavy rationale that is a fine externalization candidate by size\n"
            "// risk: but its region is dormant, so it must stay inline\n"
            "// future: [[Some Day Thing]]\n"
            "fun dorm() {}\n")
        (root / "docs" / "atramentous").mkdir(parents=True)
        (root / "docs" / "atramentous" / "register.md").write_text(
            "| ID | status |\n|---|---|\n| GhostRow | SCAFFOLD |\n")

        # --- density-tier fixtures (no growth; over-density is budget, not age) ---
        (root / "anchor.kt").write_text("fun anchor() {}\n")  # resolves [[anchor]]
        # per-function over-density: two assistive nodes on one function (> max 1)
        (root / "zoneFunc").mkdir()
        (root / "zoneFunc" / "f.kt").write_text(
            "// atra: [[anchor]] one\n"
            "// atra: [[anchor]] two\n"
            "fun densely() {}\n"
            "fun sparse() {}\n"
            "// atra: [[anchor]] solo\n")
        # file over-density: 30 breadcrumbs (1/function) over 30 code lines, budget 1
        (root / "zoneDense").mkdir()
        (root / "zoneDense" / "d.kt").write_text(
            "".join(f"// atra: [[anchor]] n{k}\nfun c{k}() {{}}\n" for k in range(30)))
        # at-budget: 30 code lines, a single breadcrumb -> within ratio, no flag
        (root / "zoneOK").mkdir()
        (root / "zoneOK" / "o.kt").write_text(
            "// atra: [[anchor]] the one note this file needs\n"
            + "".join(f"fun ok{k}() {{}}\n" for k in range(30)))
        # guardrail must NEVER be budget-counted: dense SAFETY block, no flag
        (root / "zoneGuard").mkdir()
        (root / "zoneGuard" / "g.kt").write_text(
            "// ATRAMENTOUS SAFETY\n"
            "// why: never lose user data\n"
            "// do-not: skip the atomic rename\n"
            "// invariant: temp fsynced before rename\n"
            "fun save() {}\n")
        # store-pointer resolution: existing slug resolves, ghost slug is a dead link
        (root / "docs" / "atramentous" / "store").mkdir()
        (root / "docs" / "atramentous" / "store" / "existing-note.md").write_text(
            "---\nid: existing-note\ntitle: A real store note\nstatus: REFERENCE\n---\n\n"
            "why: exists so a [[store:existing-note]] pointer resolves in the selftest.\n")
        (root / "zonePtr").mkdir()
        (root / "zonePtr" / "p.kt").write_text(
            "// atra: see [[store:existing-note]] — losing this breaks the parity check\n"
            "fun a() {}\n"
            "// atra: see [[store:ghost-note]] — points at no note\n"
            "fun b() {}\n")
        # CONSULT nodes: a gated one (named phase) is fine; a gateless one ("later")
        # is the deferred-consultation-by-neglect failure -> consult-gateless.
        (root / "zoneConsult").mkdir()
        (root / "zoneConsult" / "c.kt").write_text(
            "// ATRAMENTOUS CONSULT\n"
            "// why: panel widths are a feel-call\n"
            "// default: 280px side / 1fr main — provisional, in effect now\n"
            "// gate: [[M12 UI Polish]] — batch a human feel-test here\n"
            "// ask: do these proportions feel right?\n"
            "fun goodConsult() {}\n"
            "// ATRAMENTOUS CONSULT\n"
            "// why: deferred but ungated\n"
            "// default: provisional\n"
            "// gate: later\n"
            "// ask: feel right?\n"
            "fun badConsult() {}\n")

        git("add", "-A"); git("commit", "-qm", "seed")

        # development moves ONLY in zoneA — 6 commits grow past its branch point
        for k in range(6):
            (root / "zoneA" / f"grow{k}.kt").write_text(f"fun g{k}() {{}}\n")
            git("add", "-A"); git("commit", "-qm", f"grow {k}")

        # thresholds in COMMITS: aging fires at >3 neighborhood commits; the
        # externalize dial is set low (>3) so the grown zone trips it.
        f = scan(str(root), age_commits=3, decision_commits=3, future_age_commits=3,
                 max_per_func=1, node_line_ratio=25, density_floor=1,
                 externalize_threshold=3, heavy_node_lines=4)
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

        # --- Stage 2: over-density (budget) ---
        od = [x for x in f if x["kind"] == "over-density"]
        # per-function: two nodes on one function flags
        assert any("zoneFunc" in x["loc"] for x in od), "missed per-function over-density"
        # file-level: dense file flags at file granularity (loc == file, no :line)
        assert any(x["loc"] == os.path.join("zoneDense", "d.kt") for x in od), "missed file over-density"
        # at-budget file does NOT flag
        assert not any("zoneOK" in x["loc"] for x in od), "false over-density on at-budget file"
        # guardrails are NEVER budget-counted
        assert not any("zoneGuard" in x["loc"] for x in od), "wrongly counted a guardrail toward density"
        # promotion suggestion is emitted, deterministically
        assert all("promote lowest-value" in x["detail"] or "consolidate" in x["detail"]
                   for x in od), "over-density missing promotion suggestion"
        # --- store-pointer resolution ---
        assert any(x["kind"] == "unresolved-link" and "ghost-note" in x["detail"] for x in f), \
            "missed dead store pointer"
        assert not any(x["kind"] == "unresolved-link" and "existing-note" in x["detail"] for x in f), \
            "wrongly flagged a valid store pointer"

        # --- Stage 3: should-externalize (growth dial) ---
        se = [x for x in f if x["kind"] == "should-externalize"]
        # zoneA grew past its heavy node -> externalize suggested
        assert any("zoneA" in x["loc"] and "a.kt" in x["loc"] for x in se), "missed should-externalize in grown zone"
        # dormant zoneDorm heavy-but-still node -> never externalized
        assert not any("zoneDorm" in x["loc"] for x in se), "wrongly externalized a dormant heavy node"
        # a guardrail in the grown zone is NEVER externalized
        assert not any("safety" in x["loc"].lower() for x in se), "wrongly externalized a guardrail"

        # --- Phase 2: consult-gateless (deferred-consultation honesty) ---
        cg = [x for x in f if x["kind"] == "consult-gateless"]
        # the gateless CONSULT ("gate: later") flags; the [[M12 ...]]-gated one does not
        assert any("zoneConsult" in x["loc"] for x in cg), "missed gateless CONSULT"
        assert len([x for x in cg if "zoneConsult" in x["loc"]]) == 1, \
            "consult-gateless should fire once: the gated CONSULT must NOT flag"

        print("selftest ok:", sorted(kinds))
        return 0


if __name__ == "__main__":
    sys.exit(main())
