"""
models.py — Pydantic request/response schemas.
"""

from pydantic import BaseModel


class BulletsPayload(BaseModel):
    """
    Sent by the AI service (your friend's code) to /generate-pdf.
    Keys are marker names WITHOUT the << >> brackets.
    Values are plain rewritten bullet text.

    Example:
        {
          "bullets": {
            "BULLET_EXP_1_1": "Spearheaded product strategy for a RAG system ...",
            "BULLET_EXP_1_2": "Established KPIs and latency benchmarks ...",
            ...
          }
        }
    """
    bullets: dict[str, str]


class BulletsResponse(BaseModel):
    """
    Returned by GET /bullets.
    The AI service reads this to know what to rewrite.
    """
    bullets: dict[str, str]
