import re
from app.latex.bold import apply_bold


def inject_bullets(tex_source: str, rewritten: dict[str, str]) -> str:
    """
    Apply bold post-processing to each rewritten bullet, then replace
    every <<MARKER>> token in the .tex source with the formatted text.

    Args:
        tex_source:  Full .tex string containing <<MARKER>> tokens.
        rewritten:   { "BULLET_EXP_1_1": "plain rewritten text...", ... }

    Returns:
        Final .tex source with all markers replaced.

    Raises:
        ValueError: if any <<BULLET_*>> marker survives (missing from dict).
    """
    source = tex_source

    for marker, plain_text in rewritten.items():
        token = f"<<{marker}>>"
        if token not in source:
            continue
        source = source.replace(token, apply_bold(plain_text))

    remaining = re.findall(r"<<BULLET_[^>]+>>", source)
    if remaining:
        raise ValueError(
            f"Markers not replaced (missing from rewritten dict): {remaining}"
        )

    return source
