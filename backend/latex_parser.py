"""
latex_parser.py

Reads the marked LaTeX template and extracts the original bullet text
for each <<BULLET_*>> marker. This dict is what gets sent to the AI.
"""

import re
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "resume_marked.tex"

# Matches <<BULLET_XYZ>> followed by the bullet text up to the closing }
# Works because bullet text in the template is plain (no nested braces)
_MARKER_RE = re.compile(r"<<(BULLET_[^>]+)>>([^}]+)")

# LaTeX sequences to strip when producing plain text for the AI
_LATEX_SUBS = [
    (re.compile(r"\$\\rightarrow\$"), "→"),
    (re.compile(r"\\textasciitilde(?:\{\})?"), "~"),
    (re.compile(r"\\%"), "%"),
    (re.compile(r"\\&"), "&"),
    (re.compile(r"---"), "—"),
    (re.compile(r"--"), "–"),
]


def _to_plain(latex_text: str) -> str:
    """Strip minimal LaTeX sequences so the AI sees clean plain text."""
    text = latex_text.strip()
    for pattern, replacement in _LATEX_SUBS:
        text = pattern.sub(replacement, text)
    return text


def extract_bullets(tex_source: str) -> dict[str, str]:
    """
    Parse the marked .tex source and return a dict of:
        { "BULLET_EXP_1_1": "plain text of bullet ...", ... }

    This is the payload to hand off to the AI for rewriting.
    """
    bullets: dict[str, str] = {}
    for match in _MARKER_RE.finditer(tex_source):
        marker = match.group(1)
        raw_text = match.group(2)
        bullets[marker] = _to_plain(raw_text)
    return bullets


def list_markers(tex_source: str) -> list[str]:
    """Return all marker names found in the template, in order."""
    return [m.group(1) for m in _MARKER_RE.finditer(tex_source)]


def load_template(path: Path = TEMPLATE_PATH) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    source = load_template()
    bullets = extract_bullets(source)
    for marker, text in bullets.items():
        print(f"[{marker}]\n  {text[:80]}...\n")
