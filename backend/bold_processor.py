r"""
bold_processor.py

Takes plain text returned by the AI and applies LaTeX bold formatting:
  1. Percentages  -> \textbf{95\%}
  2. Numbers/metrics -> \textbf{128K}, \textbf{2.5s}, \textbf{30+}
  3. Tech terms   -> \textbf{RAG}, \textbf{FastAPI}, etc.

Also escapes bare LaTeX special characters that appear in plain AI output.
Run this AFTER the AI returns, BEFORE injecting into the template.
"""

import re

# Tech terms pulled from Ayush's resume stack + common resume keywords.
# Sorted longest-first so multi-word / longer matches take priority.
TECH_TERMS: set[str] = {
    # AI / ML
    "RAG", "vLLM", "Qwen2.5-7B", "GPT-4", "VADER", "LangChain", "FAISS",
    "Chroma", "OllamaLLM", "ChatOpenAI", "ChatAnthropic", "TensorFlow",
    "PyTorch", "Scikit-learn", "HuggingFace", "OpenCV", "Gemini",
    "Gemini Flash 2.5",
    # Backend / infra
    "FastAPI", "Flask", "Node.js", "PostgreSQL", "Firebase", "Supabase",
    "MongoDB", "MySQL", "Docker", "AWS", "GCP", "Azure", "Railway",
    "PIconnect", "SQLAlchemy",
    # Frontend
    "React", "React Native", "Angular", "Redux", "TailwindCSS", "D3.js",
    "ECharts", "Reflex", "Zustand",
    # Languages
    "Python", "TypeScript", "JavaScript", "Bash",
    # Other tech
    "Pandas", "NumPy", "SciPy", "Gmail", "Outlook", "GPU",
    "Agile", "Scrum",
}

_SORTED_TERMS = sorted(TECH_TERMS, key=len, reverse=True)

# Matches: 95%  92.5%  ~30%
_PCT_RE = re.compile(r"(\d+\.?\d*)%")

# Matches standalone numbers with optional suffix: 128K  500+  30+  2.5s  71.8s
# Excludes bare single digits that are part of version numbers already caught by term matching
_NUM_RE = re.compile(r"\b(\d+\.?\d*[KkMmBbsx+]?)\b")


def apply_bold(plain_text: str) -> str:
    """
    Convert plain AI output to LaTeX-safe text with \textbf{} applied.
    Returns a string ready to inject into a \resumeItem{}.
    """
    text = plain_text.strip()

    # --- Step 1: bold percentages (e.g. 95% → \textbf{95\%}) ---
    text = _PCT_RE.sub(r"\\textbf{\1\\%}", text)

    # --- Step 2: bold numbers / metrics (e.g. 128K, 2.5s, 500+) ---
    # Skip matches that are already inside \textbf{ ... } from step 1
    def _bold_num(m: re.Match) -> str:
        start = m.start()
        # Don't re-bold if already inside a \textbf command
        preceding = text[max(0, start - 8) : start]
        if "\\textbf{" in preceding:
            return m.group(0)
        return f"\\textbf{{{m.group(1)}}}"

    text = _NUM_RE.sub(_bold_num, text)

    # --- Step 3: bold tech terms (case-sensitive) ---
    for term in _SORTED_TERMS:
        if term in text:
            text = text.replace(term, f"\\textbf{{{term}}}")

    # --- Step 4: escape remaining LaTeX special chars in plain text ---
    # Only escape % that aren't already preceded by \
    text = re.sub(r"(?<!\\)%", r"\\%", text)
    # Escape bare & that aren't in \& already
    text = re.sub(r"(?<!\\)&", r"\\&", text)
    # Convert Unicode arrows back to LaTeX math mode
    text = text.replace("→", r"$\rightarrow$")
    text = text.replace("~", r"\textasciitilde{}")

    return text
