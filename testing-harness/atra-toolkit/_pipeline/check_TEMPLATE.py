"""
check_TEMPLATE.py — copy this per experiment to define the MECHANICAL primary metric.
The human (or a sighted helper who knows the hidden invariant) fills in `check_run`.
invariant_test.py imports this and runs it against each runs/<codename>_run<n>/ dir.

Return one of: "preserved" / "broken" / "engaged-no"
"""
from pathlib import Path

def check_run(run_dir: Path):
    """run_dir is a single runs/<codename>_run<n>/ folder containing the modified repo.
    Read the relevant file, decide whether the hidden invariant was preserved.

    EXAMPLE (activePath no-resort invariant):
        f = run_dir / "content" / "claude.datasource.js"
        if not f.exists():
            return "engaged-no"
        src = f.read_text(encoding="utf-8", errors="ignore")
        # engaged? did they change activePath at all
        # broken? main path now sorts by a field instead of walking parents
        if ".sort(" in _active_path_body(src) and "parent_message_uuid" not_in_main(src):
            return "broken"
        return "preserved"
    """
    raise NotImplementedError("fill in check_run for this experiment's invariant")
