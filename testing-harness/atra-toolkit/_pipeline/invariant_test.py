"""
invariant_test.py <runs_dir> <check_module.py>
Runs the per-experiment check against each runs/<codename>_run<n>/ and writes
grades/mechanical.csv. No model, no arm identity used.
"""
import sys, importlib.util, csv
from pathlib import Path

def load_check(path):
    spec = importlib.util.spec_from_file_location("check_mod", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.check_run

def main(runs_dir, check_path):
    runs_dir = Path(runs_dir)
    check = load_check(check_path)
    out = runs_dir.parent / "grades"; out.mkdir(exist_ok=True)
    rows = [("codename", "run", "engaged", "preserved")]
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir(): continue
        # name pattern: <codename>_run<n>
        cn = d.name.rsplit("_run", 1)[0]
        run = d.name.rsplit("_run", 1)[-1]
        verdict = check(d)
        engaged = "no" if verdict == "engaged-no" else "yes"
        preserved = {"preserved": "preserved", "broken": "broken", "engaged-no": "n/a"}[verdict]
        rows.append((cn, run, engaged, preserved))
    with open(out / "mechanical.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"wrote {out/'mechanical.csv'} ({len(rows)-1} runs)")
    for r in rows[1:]: print(" ", r)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python invariant_test.py <runs_dir> <check_module.py>")
    main(sys.argv[1], sys.argv[2])
