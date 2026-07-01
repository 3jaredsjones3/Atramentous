"""
selftest.py — proves the toolkit on synthetic data BEFORE any real repo.
Builds a tiny fixture repo containing the hard cases, then runs the self-tests
from the spec plus regression tests found during review. Exits nonzero if any fail.

Run: python selftest.py
"""
import sys, shutil, json, subprocess
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from strip_lib import strip_full, strip_links_only, code_lines_of
import verify as verifymod
import support_lib

ROOT = HERE / "_selftest_work"


# ---- the fixture: arm C (fully annotated), with every hard case ----
FILE_JS = r'''// data source for the thing
function buildEndpoint(org) {
  return `/api/${org}/x`;
}

// ATRAMENTOUS  SPINE
// why:       walking parent links from the active leaf is the ONLY correct order.
// invariant: the active path is defined SOLELY by the parent-walk; NO field-based
//            ordering is valid (any sort by index/timestamp leaks branches).
// do-not:    sort by index, orderHint, or created_at; iterate in array order
// related:   [[SPINE No Resort]]
function activePath(data) {
  const re = /\[\[\^\]\]/;            // <- CODE containing [[ : must survive
  const tag = '[[Attachment]]';        // <- CODE containing [[ : must survive
  const byId = new Map();
  return byId;
}

// atra: [[Tool Description]] — the one-liner mapping lives here
function toolDesc(name) {
  return name;  // ordinary comment that MUST survive
}

// [[Bare Link One]] [[Bare Link Two]]
function tail() { return 1; }
'''

FILE_PY = r'''# ordinary module comment that must survive
def f(x):
    # [[Not An Annotation Because]] this line also has code:
    y = x  # trailing ordinary comment
    return y

# ATRAMENTOUS  SAFETY
# why:       this guard prevents a crash
# invariant: never call g() with None
# do-not:    pass None to g
# enforced-by: [[test:g-null-guard]]
def g(z):
    return z + 1
'''

STORE_NOTE = "# store note\nsome externalized rationale [[Linked Thing]]\n"


def build_fixture():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    armC = ROOT / "arm_C"
    (armC / "content").mkdir(parents=True)
    (armC / "content" / "ds.js").write_text(FILE_JS, encoding="utf-8")
    (armC / "lib.py").write_text(FILE_PY, encoding="utf-8")
    (armC / "docs" / "atramentous" / "store").mkdir(parents=True)
    (armC / "docs" / "atramentous" / "store" / "x.md").write_text(STORE_NOTE, encoding="utf-8")
    return armC


# expected "bare" code for ds.js: every annotation line gone, all code (incl [[-code]]
# and the ordinary comments) preserved.
def expected_bare_js_codelines():
    return [
        "// data source for the thing",
        "function buildEndpoint(org) {",
        "  return `/api/${org}/x`;",
        "}",
        "",
        "function activePath(data) {",
        r"  const re = /\[\[\^\]\]/;            // <- CODE containing [[ : must survive",
        "  const tag = '[[Attachment]]';        // <- CODE containing [[ : must survive",
        "  const byId = new Map();",
        "  return byId;",
        "}",
        "",
        "function toolDesc(name) {",
        "  return name;  // ordinary comment that MUST survive",
        "}",
        "",
        "function tail() { return 1; }",
    ]


def test1_strip_full_safety(armC):
    out = ROOT / "arm_A"
    strip_full(armC, out)
    # docs/atramentous gone
    assert not (out / "docs" / "atramentous").exists(), "atra docs not removed"
    # ds.js code lines match expected (ignoring blank-run collapse at edges)
    got = [l for l in (out / "content" / "ds.js").read_text(encoding="utf-8").split("\n")]
    exp = expected_bare_js_codelines()
    got_nonblank = [l for l in got if l.strip() != ""]
    exp_nonblank = [l for l in exp if l.strip() != ""]
    assert got_nonblank == exp_nonblank, f"strip_full mismatch:\nGOT {got_nonblank}\nEXP {exp_nonblank}"
    # the [[-bearing CODE lines survive
    body = (out / "content" / "ds.js").read_text(encoding="utf-8")
    assert r"/\[\[\^\]\]/" in body, "regex literal with [[ was stripped!"
    assert "'[[Attachment]]'" in body, "template string with [[ was stripped!"
    # ordinary comments survive
    assert "ordinary comment that MUST survive" in body
    assert "// data source for the thing" in body
    # py ordinary comments survive, annotations gone
    pybody = (out / "lib.py").read_text(encoding="utf-8")
    assert "ordinary module comment that must survive" in pybody
    assert "trailing ordinary comment" in pybody
    assert "[[Not An Annotation Because]]" in pybody, "code-bearing [[ line in py stripped!"
    assert "ATRAMENTOUS" not in pybody and "enforced-by" not in pybody
    return "PASS"


def test2_links_only(armC):
    out = ROOT / "arm_B"
    strip_links_only(armC, out)
    body = (out / "content" / "ds.js").read_text(encoding="utf-8")
    # the SPINE block collapses to its links only; prose gone
    assert "[[SPINE No Resort]]" in body, "block link not preserved in B"
    assert "walking parent links" not in body, "prose survived in B"
    assert "do-not" not in body, "guardrail field survived in B"
    # breadcrumb link kept
    assert "[[Tool Description]]" in body
    # bare link comment kept
    assert "[[Bare Link One]]" in body and "[[Bare Link Two]]" in body
    # code with [[ still intact
    assert r"/\[\[\^\]\]/" in body and "'[[Attachment]]'" in body
    # ordinary comments still intact
    assert "ordinary comment that MUST survive" in body
    return "PASS"


def test3_verify(armC):
    # build clean = arm_A (since A is the additive-free baseline == original)
    clean = ROOT / "clean"
    if clean.exists(): shutil.rmtree(clean)
    shutil.copytree(ROOT / "arm_A", clean)
    fails = verifymod.verify(clean, ROOT / "arm_A", ROOT / "arm_B", ROOT / "arm_C")
    assert not fails, f"verify should PASS on clean arms, got: {fails}"
    # now inject a one-char CODE change into arm_B and confirm verify FAILS
    bfile = ROOT / "arm_B" / "content" / "ds.js"
    txt = bfile.read_text(encoding="utf-8").replace("return byId;", "return byId ;")
    bfile.write_text(txt, encoding="utf-8")
    fails2 = verifymod.verify(clean, ROOT / "arm_A", ROOT / "arm_B", ROOT / "arm_C")
    assert fails2, "verify FAILED to catch an injected code change in arm B!"
    # restore B
    strip_links_only(armC, ROOT / "arm_B")
    return "PASS"


def test4_codename(armC):
    blind = ROOT / "blind"
    if blind.exists(): shutil.rmtree(blind)
    # drop a leak file into arm_A to confirm it gets scrubbed
    (ROOT / "arm_A" / "CHANGES_SUMMARY.md").write_text("I edited arm A", encoding="utf-8")
    (ROOT / "task.md").write_text("do the thing", encoding="utf-8")
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        support_lib.codename(ROOT / "arm_A", ROOT / "arm_B", ROOT / "arm_C", blind, ROOT / "task.md")
    printed = buf.getvalue()
    key = json.loads((blind / "key.json").read_text(encoding="utf-8"))
    # mapping never printed
    for cn, arm in key.items():
        assert f"{cn}: {arm}" not in printed and f'"{cn}": "{arm}"' not in printed, "mapping leaked to stdout"
    assert "A" not in printed.split("codenames:")[1] if "codenames:" in printed else True
    # 3 codenamed dirs exist
    dirs = [d for d in blind.iterdir() if d.is_dir()]
    assert len(dirs) == 3, f"expected 3 codenamed dirs, got {len(dirs)}"
    # leak file scrubbed in whichever dir is arm A
    arm_to_cn = {v: k for k, v in key.items()}
    a_dir = blind / arm_to_cn["A"]
    assert not (a_dir / "CHANGES_SUMMARY.md").exists(), "leak file not scrubbed from codenamed arm A"
    # the arm-A and arm-B codenamed copies contain no full ATRAMENTOUS blocks
    for arm in ("A", "B"):
        d = blind / arm_to_cn[arm]
        for p in d.rglob("*.js"):
            assert "ATRAMENTOUS" not in p.read_text(encoding="utf-8"), f"residual block in {arm}"
    # key round-trips: collate can map back
    assert set(key.values()) == {"A", "B", "C"}
    return "PASS"


def test5_bundle_refuses_key():
    test_dir = ROOT
    (test_dir / "runs").mkdir(exist_ok=True)
    (test_dir / "runs" / "dummy.txt").write_text("x", encoding="utf-8")
    (test_dir / "rubric.md").write_text("rubric", encoding="utf-8")
    # put a key.json inside runs to simulate accidental inclusion
    (test_dir / "runs" / "key.json").write_text("{}", encoding="utf-8")
    try:
        support_lib.make_grader_bundle(test_dir, ROOT / "bundle.zip")
    except SystemExit as e:
        (test_dir / "runs" / "key.json").unlink()
        return "PASS"
    (test_dir / "runs" / "key.json").unlink()
    raise AssertionError("make_grader_bundle did NOT refuse a key.json in the bundle")


def test6_byte_preservation():
    """Regression: strip_full on an annotation-FREE file must preserve bytes exactly —
    no blank-run collapse, no trailing-newline forcing. (Bug found in review.)"""
    work = ROOT / "_byte"
    if work.exists(): shutil.rmtree(work)
    src = work / "src"; src.mkdir(parents=True)
    # 3 blank lines, no trailing newline, no annotations anywhere
    original = "a();\n\n\n\nb();"
    (src / "f.js").write_text(original, encoding="utf-8")
    strip_full(src, work / "out")
    got = (work / "out" / "f.js").read_text(encoding="utf-8")
    assert got == original, f"strip_full mutated an annotation-free file: {got!r} != {original!r}"
    return "PASS"


def test7_markdown_heading():
    """Regression: a Markdown '# [[Heading]]' is a heading, not a # comment, and must
    survive stripping. (Bug found in review — # treated as comment everywhere.)"""
    work = ROOT / "_md"
    if work.exists(): shutil.rmtree(work)
    src = work / "src"; src.mkdir(parents=True)
    md = "# [[Some Heading]]\n\nbody text [[Inline Ref]] in prose\n\n## [[Another]]\n"
    (src / "README.md").write_text(md, encoding="utf-8")
    # also a real HTML-comment annotation in markdown that SHOULD be stripped
    md2 = "# Title\n\n<!-- atra: [[Note]] — keep this out of arm A -->\ntext\n"
    (src / "doc.md").write_text(md2, encoding="utf-8")
    strip_full(src, work / "out")
    got = (work / "out" / "README.md").read_text(encoding="utf-8")
    assert got == md, f"markdown headings damaged by strip: {got!r}"
    got2 = (work / "out" / "doc.md").read_text(encoding="utf-8")
    assert "atra:" not in got2, "real HTML-comment annotation not stripped from markdown"
    assert "# Title" in got2 and "text" in got2, "markdown content damaged"
    return "PASS"


def test8_html_links_only_well_formed():
    """Regression: links-only reduction in Markdown/HTML must emit a CLOSED HTML
    comment, not '<!-- [[X]]' which comments out the rest of the document."""
    work = ROOT / "_html_links"
    if work.exists(): shutil.rmtree(work)
    src = work / "src"; src.mkdir(parents=True)
    md = ("# Title\n\n"
          "<!-- ATRAMENTOUS NOTE [[Doc Node]] -->\n"
          "<!-- why: this rationale should disappear in B -->\n"
          "after\n")
    (src / "README.md").write_text(md, encoding="utf-8")
    strip_links_only(src, work / "out")
    got = (work / "out" / "README.md").read_text(encoding="utf-8")
    assert "<!-- [[Doc Node]] -->" in got, f"HTML link comment not closed: {got!r}"
    assert "<!-- [[Doc Node]]\n" not in got, f"malformed HTML comment emitted: {got!r}"
    assert "why:" not in got and "after" in got, "links-only reduction damaged markdown body"
    return "PASS"


def test9_crlf_preservation():
    """Regression: transformed files must preserve CRLF bytes, even when run on
    Windows. Use bytes here so the test itself cannot hide newline translation."""
    work = ROOT / "_crlf"
    if work.exists(): shutil.rmtree(work)
    src = work / "src"; src.mkdir(parents=True)

    no_annotation = b"a();\r\n\r\n\r\nb();"
    (src / "plain.js").write_bytes(no_annotation)
    annotated = (b"a();\r\n"
                 b"// ATRAMENTOUS NOTE [[CRLF Node]]\r\n"
                 b"// why: remove this but keep CRLF style\r\n"
                 b"b();\r\n")
    (src / "annotated.js").write_bytes(annotated)

    strip_full(src, work / "bare")
    assert (work / "bare" / "plain.js").read_bytes() == no_annotation, "plain CRLF file mutated"
    assert (work / "bare" / "annotated.js").read_bytes() == b"a();\r\nb();\r\n", \
        "CRLF code lines not preserved after strip_full"

    strip_links_only(src, work / "links")
    assert (work / "links" / "plain.js").read_bytes() == no_annotation, "links-only mutated plain CRLF file"
    assert (work / "links" / "annotated.js").read_bytes() == \
        b"a();\r\n// [[CRLF Node]]\r\nb();\r\n", "links-only did not preserve CRLF style"
    return "PASS"


def test10_unknown_extension_fails_closed():
    """Regression: unknown file types should not accept every comment marker. A file
    with no known syntax must be left alone rather than risk deleting real content."""
    work = ROOT / "_unknown"
    if work.exists(): shutil.rmtree(work)
    src = work / "src"; src.mkdir(parents=True)
    text = "// ATRAMENTOUS MAYBE [[Unknown Syntax]]\n// why: unsupported extension\ncode\n"
    (src / "README").write_text(text, encoding="utf-8")
    strip_full(src, work / "out")
    got = (work / "out" / "README").read_text(encoding="utf-8")
    assert got == text, "unknown extension should fail closed by preserving bytes"
    return "PASS"


def main():
    armC = build_fixture()
    results = {}
    for name, fn in [("1 strip_full safety", lambda: test1_strip_full_safety(armC)),
                     ("2 links_only", lambda: test2_links_only(armC)),
                     ("3 verify catches drift", lambda: test3_verify(armC)),
                     ("4 codename + scrub + key", lambda: test4_codename(armC)),
                     ("5 bundle refuses key", test5_bundle_refuses_key),
                     ("6 byte preservation", test6_byte_preservation),
                     ("7 markdown heading safe", test7_markdown_heading),
                     ("8 html links-only closed", test8_html_links_only_well_formed),
                     ("9 CRLF preservation", test9_crlf_preservation),
                     ("10 unknown ext fails closed", test10_unknown_extension_fails_closed)]:
        try:
            results[name] = fn()
        except AssertionError as e:
            results[name] = f"FAIL: {e}"
        except Exception as e:
            results[name] = f"ERROR: {type(e).__name__}: {e}"
    print("\n=== SELF-TEST RESULTS ===")
    ok = True
    for k, v in results.items():
        print(f"  [{ 'OK ' if v=='PASS' else 'XX ' }] {k}: {v}")
        if v != "PASS": ok = False
    print("=========================")
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
