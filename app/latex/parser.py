import re
from pathlib import Path
from app.config import TEMPLATE_PATH

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
    Parse the marked .tex source and return:
        { "BULLET_EXP_1_1": "plain text of bullet...", ... }
    This is the payload handed to the AI for rewriting.
    """
    return {
        m.group(1): _to_plain(m.group(2))
        for m in _MARKER_RE.finditer(tex_source)
    }


def list_markers(tex_source: str) -> list[str]:
    """Return all marker names found in the template, in order."""
    return [m.group(1) for m in _MARKER_RE.finditer(tex_source)]


def load_template(path: Path = TEMPLATE_PATH) -> str:
    return path.read_text(encoding="utf-8")
