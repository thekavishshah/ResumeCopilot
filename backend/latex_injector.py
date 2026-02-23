"""
latex_injector.py

Takes the marked .tex source and a dict of AI-rewritten bullets,
applies bold post-processing to each bullet, then replaces every
<<MARKER>> with the formatted text.

Returns the final .tex source ready for pdflatex.
"""

from bold_processor import apply_bold


def inject_bullets(tex_source: str, rewritten: dict[str, str]) -> str:
    """
    Args:
        tex_source:  The full .tex string (still containing <<MARKER>> tokens).
        rewritten:   { "BULLET_EXP_1_1": "plain rewritten text...", ... }
                     Keys that don't exist in the template are silently ignored.

    Returns:
        .tex source with all matched markers replaced by bolded LaTeX text.

    Raises:
        ValueError: if any <<MARKER>> token remains after injection
                    (means a marker in the template had no matching key).
    """
    source = tex_source

    for marker, plain_text in rewritten.items():
        token = f"<<{marker}>>"
        if token not in source:
            continue
        formatted = apply_bold(plain_text)
        source = source.replace(token, formatted)

    # Safety check: no markers should survive
    import re
    remaining = re.findall(r"<<BULLET_[^>]+>>", source)
    if remaining:
        raise ValueError(
            f"Markers not replaced (missing from rewritten dict): {remaining}"
        )

    return source
