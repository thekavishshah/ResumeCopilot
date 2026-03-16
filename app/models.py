from typing import Optional
from pydantic import BaseModel, HttpUrl


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


class ScrapeRequest(BaseModel):
    """
    Request to scrape a job description from a URL.
    url: Job posting URL (supports Workday, Greenhouse, SmartRecruiters, Lever, etc.)
    """
    url: str


class ScrapeResponse(BaseModel):
    """
    Response from job description scraping.
    success: Whether scraping was successful
    title: Job title (if scraped)
    description: Full job description text (if scraped)
    qualifications: List of extracted qualifications/requirements (if scraped)
    platform: Platform name (if detected)
    url: Original URL
    error: Error message (if failed)
    """
    success: bool
    title: Optional[str] = None
    description: Optional[str] = None
    qualifications: Optional[list[str]] = None
    platform: Optional[str] = None
    url: str
    error: Optional[str] = None


class TailorFromUrlRequest(BaseModel):
    """
    Request to tailor resume from a job URL.
    url: Job posting URL (optional - if provided, will attempt to scrape)
    quals: Manual job qualifications (optional - used if URL fails or not provided)

    Either url or quals must be provided. If both provided, URL is tried first,
    then falls back to manual quals if scraping fails.
    """
    url: Optional[str] = None
    quals: Optional[list[str]] = None
