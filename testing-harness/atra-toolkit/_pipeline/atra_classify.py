"""
atra_classify.py — the shared annotation classifier.

Every strip/verify script depends on ONE question: "is this line an Atramentous
annotation, or is it code (possibly code that happens to contain [[ )?" This module
is the single source of truth for that decision, so the three scripts can never
disagree about what counts as an annotation (which is how a prior run corrupted an
arm — one stripper deleted a real code comment).

The classifier works line-by-line but is block-aware: an ATRAMENTOUS heavy block is
a sentinel line plus the contiguous field-continuation comment lines beneath it.

CODE SAFETY is the load-bearing invariant: a line is an annotation ONLY if it is a
comment matching the markers below. Code that merely contains `[[` — a regex literal
like /\\[\\[\\^\\]\\]/, a template string like '[[Attachment]]', array destructuring —
is NEVER an annotation. We key off the comment-marker + Atramentous-syntax, never off
the bare presence of brackets.
"""
import re

# Comment-line shapes we understand (line + HTML). We detect the comment marker, then
# inspect the payload after it.
_COMMENT = re.compile(r"^(\s*)(//|#|--|<!--)\s?(.*?)\s*(-->)?\s*$")
# Recognized Atramentous field names (continuation lines of a heavy block).
_FIELDS = ("why", "invariant", "related", "future", "gate", "promote-when",
           "unless", "risk", "do-not", "status", "default", "ask",
           "local-only", "annotate", "enforced-by")
_FIELD_RE = re.compile(r"^(" + "|".join(re.escape(f) for f in _FIELDS) + r")\s*:", re.I)
_SENTINEL = re.compile(r"\bATRAMENTOUS\b")
_ATRA_BREADCRUMB = re.compile(r"^atra:")
# A "pure link comment" payload is ONLY [[...]] tokens and whitespace, nothing else.
_LINK_TOKEN = re.compile(r"\[\[[^\]]+\]\]")
_PURE_LINKS = re.compile(r"^(\s*\[\[[^\]]+\]\]\s*)+$")


def _comment_payload(line, markers=None):
    """Return (indent, marker, payload) if the line is a comment, else None.
    `markers` restricts which comment markers are valid for this file type; if None,
    all known markers are accepted (back-compat)."""
    m = _COMMENT.match(line)
    if not m:
        return None
    marker = m.group(2)
    if markers is not None and marker not in markers:
        return None
    return m.group(1), marker, m.group(3)


# Which comment markers are valid per file extension. The danger this prevents:
# Markdown `# [[Heading]]` is a HEADING, not a comment — treating `#` as a comment
# marker there would strip real headings. SQL/Lua/Haskell use `--`. Most C-family
# languages use `//`. Markdown/HTML annotations must live inside <!-- -->.
#
# Unknown file types intentionally accept NO markers. That makes the stripper fail
# closed: it may leave annotations behind in an unsupported file, causing verify to
# fail, but it will not delete ordinary content from a file whose syntax we do not
# understand.
_MARKERS_BY_EXT = {
    ".py": {"#"}, ".rb": {"#"}, ".sh": {"#"}, ".bash": {"#"}, ".zsh": {"#"},
    ".ps1": {"#"}, ".psm1": {"#"}, ".yaml": {"#"}, ".yml": {"#"},
    ".toml": {"#"}, ".cfg": {"#"}, ".ini": {"#"}, ".pl": {"#"}, ".cmake": {"#"},
    ".js": {"//"}, ".jsx": {"//"}, ".ts": {"//"}, ".tsx": {"//"},
    ".mjs": {"//"}, ".cjs": {"//"}, ".mts": {"//"}, ".cts": {"//"},
    ".java": {"//"}, ".c": {"//"}, ".h": {"//"}, ".cpp": {"//"},
    ".hpp": {"//"}, ".cc": {"//"}, ".rs": {"//"}, ".go": {"//"},
    ".swift": {"//"}, ".kt": {"//"}, ".kts": {"//"}, ".scala": {"//"},
    ".cs": {"//"}, ".php": {"//"}, ".sql": {"--"}, ".lua": {"--"}, ".hs": {"--"},
    ".md": {"<!--"}, ".markdown": {"<!--"}, ".html": {"<!--"}, ".htm": {"<!--"},
    ".xml": {"<!--"}, ".vue": {"<!--", "//"}, ".svelte": {"<!--", "//"},
    ".astro": {"<!--", "//"},
}
_MARKERS_BY_NAME = {
    "dockerfile": {"#"}, "containerfile": {"#"},
    "makefile": {"#"}, "gnumakefile": {"#"},
    "cmakelists.txt": {"#"},
}


def markers_for(path):
    """Return the valid comment markers for a file path.

    Unknown extensions return an empty set, not None. That is deliberately
    conservative: unsupported syntax should fail verification by leaving annotations
    behind rather than risk deleting real content. Passing markers=None directly to
    classify_lines still means "all markers" for explicit tests/back-compat.
    """
    from pathlib import Path as _P
    q = _P(str(path))
    by_name = _MARKERS_BY_NAME.get(q.name.lower())
    if by_name is not None:
        return by_name
    return _MARKERS_BY_EXT.get(q.suffix.lower(), set())


def classify_lines(lines, markers=None):
    """Given a list of source lines, return a list of tags, one per line:
      'sentinel'  - the `// ATRAMENTOUS ...` line that opens a heavy block
      'field'     - a continuation field line belonging to an open block
      'breadcrumb'- a `// atra: ...` line
      'purelink'  - a comment whose entire payload is only [[...]] tokens
      'code'      - everything else (real code, ordinary comments, code with [[ )
    `markers`: set of valid comment markers for this file type (from markers_for()).
    Pass it so e.g. a Markdown `# [[Heading]]` is NOT treated as a comment.
    """
    tags = []
    block_open = False        # are we inside a heavy ATRAMENTOUS block?
    seen_field = False        # has the open block produced at least one field line?
    for line in lines:
        parsed = _comment_payload(line, markers)
        if parsed is None:
            # any non-comment line ends a block
            tags.append("code")
            block_open = False
            seen_field = False
            continue
        _, _, payload = parsed
        if _SENTINEL.search(payload):
            tags.append("sentinel")
            block_open = True
            seen_field = False
            continue
        if block_open:
            # Inside a block, a blank-payload comment line ends the block (blank
            # separator), UNLESS it's still clearly part of the block. We end on
            # an empty comment payload to avoid swallowing following comments.
            if payload.strip() == "":
                tags.append("code")
                block_open = False
                seen_field = False
                continue
            if _FIELD_RE.match(payload):
                tags.append("field")
                seen_field = True
                continue
            # A non-field comment line inside a block is a WRAPPED field value
            # (continuation) only if we've already seen a field and this isn't a
            # new breadcrumb/pure-link. This keeps wrapped prose (even with parens)
            # attached, while not swallowing an unrelated comment that appears
            # before any field.
            if seen_field and not _ATRA_BREADCRUMB.match(payload) \
                    and not _PURE_LINKS.match(payload):
                tags.append("field")
                continue
            # otherwise the block has ended; fall through to normal handling
            block_open = False
            seen_field = False
        if _ATRA_BREADCRUMB.match(payload):
            tags.append("breadcrumb")
            continue
        if payload and _PURE_LINKS.match(payload):
            tags.append("purelink")
            continue
        tags.append("code")
    return tags


def is_annotation(tag):
    return tag in ("sentinel", "field", "breadcrumb", "purelink")


def link_tokens(line):
    """Extract [[...]] tokens from a line (used to build arm B)."""
    return _LINK_TOKEN.findall(line)


def comment_marker(line):
    """Return the comment marker for a line, defaulting to // ."""
    p = _comment_payload(line)
    return p[1] if p else "//"
