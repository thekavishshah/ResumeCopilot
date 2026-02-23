from pydantic import BaseModel


class BulletsResponse(BaseModel):
    """Returned by GET /bullets. The AI service reads this."""
    bullets: dict[str, str]


class BulletsPayload(BaseModel):
    """
    Sent to POST /generate-pdf to bypass AI (for testing).
    Keys are marker names without << >>. Values are plain rewritten text.
    """
    bullets: dict[str, str]


class TailorRequest(BaseModel):
    """
    Sent to POST /tailor for the full pipeline.
    quals: job qualifications extracted by the Chrome extension.
    """
    quals: list[str]
