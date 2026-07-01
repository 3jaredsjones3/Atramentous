"""
verify.py — THE GATE. Confirms arms A/B/C differ ONLY in annotation lines, and that
arm A's code equals the original clean tree (so the annotation pass was additive).

  python verify.py <original_clean> <arm_A> <arm_B> <arm_C>

Exit 0 + "VERIFY PASS" only if every check passes. On failure, prints the offending
files and exits nonzero, so the pipeline stops here rather than running an invalid
experiment.
"""
import sys
from pathlib import Path
from strip_lib import code_lines_of, _iter_files


def _rel_text_files(root):
    out = {}
    for p in _iter_files(Path(root)):
        rel = p.relative_to(root)
        # skip the atra docs dir for cross-arm code comparison (only C has it)
        parts = rel.parts
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "atramentous":
            continue
        out[str(rel).replace("\\", "/")] = p
    return out


def _safe_code_lines(p):
    try:
        return code_lines_of(p)
    except (UnicodeDecodeError, ValueError):
        return None  # binary; compare by bytes elsewhere


def verify(original, arm_a, arm_b, arm_c):
    fails = []
    fa, fb, fc = _rel_text_files(arm_a), _rel_text_files(arm_b), _rel_text_files(arm_c)
    forig = _rel_text_files(original)

    # 1. same set of (non-atra-doc) files across A, B, C
    if not (set(fa) == set(fb) == set(fc)):
        only = lambda x, y: sorted(set(x) - set(y))
        fails.append(f"file sets differ. A-only={only(fa,fb)+only(fa,fc)} "
                     f"B-only={only(fb,fa)} C-only={only(fc,fa)}")

    # 2. code lines identical across A, B, C for every shared file
    for rel in sorted(set(fa) & set(fb) & set(fc)):
        ca, cb, cc = _safe_code_lines(fa[rel]), _safe_code_lines(fb[rel]), _safe_code_lines(fc[rel])
        if ca is None:  # binary: compare bytes
            if not (fa[rel].read_bytes() == fb[rel].read_bytes() == fc[rel].read_bytes()):
                fails.append(f"binary differs across arms: {rel}")
            continue
        if ca != cb:
            fails.append(f"code lines differ A vs B: {rel} ({_first_diff(ca, cb)})")
        if ca != cc:
            fails.append(f"code lines differ A vs C: {rel} ({_first_diff(ca, cc)})")

    # 3. arm A == original (annotation was additive — no code touched)
    if set(fa) != set(forig):
        fails.append("arm A file set != original (annotation added/removed files)")
    for rel in sorted(set(fa) & set(forig)):
        if fa[rel].read_bytes() != forig[rel].read_bytes():
            # allow it ONLY if the difference is purely annotation lines that A failed
            # to strip — but A should be fully stripped, so any byte diff is a fail
            fails.append(f"arm A differs from original (non-additive annotation): {rel}")

    return fails


def _first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f"line {i}: {x!r} != {y!r}"
    return f"length {len(a)} != {len(b)}"


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: python verify.py <original_clean> <arm_A> <arm_B> <arm_C>")
    fails = verify(*sys.argv[1:5])
    if fails:
        print("VERIFY FAIL:")
        for f in fails[:50]:
            print("  -", f)
        sys.exit(1)
    print("VERIFY PASS — arms differ only in annotations; arm A matches original.")
