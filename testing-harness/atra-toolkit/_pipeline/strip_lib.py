"""
strip_full.py / strip_links_only.py — derive arm A (bare) and arm B (links-only)
from arm C (full annotations) by mechanical removal, leaving code bytes identical.

Run as:
  python strip_full.py <in_dir> <out_dir>
  python strip_links_only.py <in_dir> <out_dir>

Both reuse atra_classify so they can never disagree with verify about what a code
line is. docs/atramentous/ is removed wholesale for arm A and B; the inline links
that matter remain in source files for arm B.

Byte-safety rule: this module transforms UTF-8 text by line records with original
line endings preserved. It never uses text-mode writes for transformed files, so a
Windows run cannot silently convert LF/CRLF and invalidate the experiment.
"""
import re
import sys
import shutil
from pathlib import Path
from atra_classify import classify_lines, is_annotation, link_tokens, comment_marker, markers_for

SKIP_DIRS = {".git", "node_modules"}
ATRA_DOCS = ("docs", "atramentous")
_EOL_RE = re.compile(r"(\r\n|\n|\r)$")


def _iter_files(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.parts):
            yield p


def _is_atra_doc(rel: Path):
    parts = rel.parts
    return len(parts) >= 2 and parts[0] == ATRA_DOCS[0] and parts[1] == ATRA_DOCS[1]


def _decode_utf8_records(p: Path):
    """Return decoded line records with original EOLs preserved.

    Raises UnicodeDecodeError for non-UTF-8 files, which callers treat as binary and
    copy/compare by bytes. A line record includes its original line terminator, if it
    had one; an empty file returns [].
    """
    text = p.read_bytes().decode("utf-8", errors="strict")
    return text.splitlines(keepends=True)


def _strip_eol(line: str) -> str:
    return _EOL_RE.sub("", line)


def _line_eol(line: str) -> str:
    m = _EOL_RE.search(line)
    return m.group(1) if m else ""


def _write_utf8_records(path: Path, records):
    # Binary write avoids platform newline translation on Windows.
    path.write_bytes("".join(records).encode("utf-8"))


def _classify_records(records, src: Path):
    return classify_lines([_strip_eol(r) for r in records], markers_for(src))


def strip_full(in_dir, out_dir):
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    for src in _iter_files(in_dir):
        rel = src.relative_to(in_dir)
        if _is_atra_doc(rel):
            continue  # drop the whole store/register
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            records = _decode_utf8_records(src)
        except UnicodeDecodeError:
            shutil.copy2(src, dst)  # binary/non-UTF-8: copy as-is
            continue
        tags = _classify_records(records, src)
        kept = [rec for rec, tg in zip(records, tags) if not is_annotation(tg)]
        # SURGICAL: remove ONLY annotation line records. No blank-run collapse, no
        # trailing newline forcing, no newline translation. Cosmetic blank scars are
        # acceptable; mutating original bytes is not.
        _write_utf8_records(dst, kept)
    return out_dir


def strip_links_only(in_dir, out_dir):
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    for src in _iter_files(in_dir):
        rel = src.relative_to(in_dir)
        if _is_atra_doc(rel):
            continue
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            records = _decode_utf8_records(src)
        except UnicodeDecodeError:
            shutil.copy2(src, dst)
            continue
        tags = _classify_records(records, src)
        out_records = _reduce_to_links(records, tags)
        # No global blank-collapse: preserve original spacing and original line endings.
        # _reduce_to_links replaces each annotation block with one syntactically valid
        # comment line using the removed block's own line-ending style.
        _write_utf8_records(dst, out_records)
    return out_dir


def _format_link_comment(indent: str, marker: str, links) -> str:
    joined = " ".join(links)
    if marker == "<!--":
        return f"{indent}<!-- {joined} -->"
    return f"{indent}{marker} {joined}"


def _reduce_to_links(records, tags):
    """Replace each annotation BLOCK with one comment line carrying only its links.

    A block = a maximal run of annotation lines. If the run has no links, drop it.
    The replacement line keeps the indentation and comment syntax of the first line in
    the block, and the line ending of the last line in the block. HTML comments are
    closed (`<!-- [[X]] -->`) so Arm B cannot accidentally comment out the file tail.
    """
    out, i, n = [], 0, len(records)
    stripped = [_strip_eol(r) for r in records]
    while i < n:
        if is_annotation(tags[i]):
            j = i
            toks = []
            indent = stripped[i][:len(stripped[i]) - len(stripped[i].lstrip())]
            marker = comment_marker(stripped[i])
            while j < n and is_annotation(tags[j]):
                toks.extend(link_tokens(stripped[j]))
                j += 1
            if toks:
                # dedupe preserving order
                seen, uniq = set(), []
                for t in toks:
                    if t not in seen:
                        seen.add(t)
                        uniq.append(t)
                eol = _line_eol(records[j - 1])
                out.append(_format_link_comment(indent, marker, uniq) + eol)
            i = j
        else:
            out.append(records[i])
            i += 1
    return out


def code_lines_of(path: Path):
    """Used by verify: return CODE line records (annotations removed) for a file.

    The returned strings include original line endings. That intentionally lets verify
    catch accidental CRLF/LF drift in code lines across arms.
    """
    records = _decode_utf8_records(path)
    tags = _classify_records(records, path)
    return [rec for rec, tg in zip(records, tags) if not is_annotation(tg)]


if __name__ == "__main__":
    name = Path(sys.argv[0]).stem
    if len(sys.argv) != 3:
        sys.exit(f"usage: python {name}.py <in_dir> <out_dir>")
    if name == "strip_full":
        out = strip_full(sys.argv[1], sys.argv[2])
    elif name == "strip_links_only":
        out = strip_links_only(sys.argv[1], sys.argv[2])
    else:
        sys.exit("run as strip_full.py or strip_links_only.py")
    print(f"wrote {out}")
