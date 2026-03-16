from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.latex.parser import extract_bullets, load_template
from app.latex.injector import inject_bullets
from app.latex.compiler import compile_pdf, CompilationError
from app.ai.rewriter import rewrite_all
from app.models import (
    BulletsPayload,
    BulletsResponse,
    TailorRequest,
    ScrapeRequest,
    ScrapeResponse,
    TailorFromUrlRequest,
)
from app.scraper import scrape_job_description

router = APIRouter()


def _get_template() -> str:
    try:
        return load_template()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Template not found: {e}")


def _pdf_response(tex_source: str, rewritten: dict[str, str]) -> Response:
    try:
        final_tex = inject_bullets(tex_source, rewritten)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        pdf_bytes = compile_pdf(final_tex)
    except CompilationError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"},
    )


@router.get("/bullets", response_model=BulletsResponse)
def get_bullets():
    """
    Returns the original bullet text for every <<BULLET_*>> marker.
    The AI service calls this to know what to rewrite.
    """
    source = _get_template()
    return BulletsResponse(bullets=extract_bullets(source))


@router.post("/generate-pdf")
def generate_pdf(payload: BulletsPayload):
    """
    Accepts pre-rewritten bullets (bypasses AI). Useful for testing the
    LaTeX pipeline without a Gemini API key.
    """
    source = _get_template()
    return _pdf_response(source, payload.bullets)


@router.post("/tailor")
def tailor(request: TailorRequest):
    """
    Full pipeline: job qualifications in, tailored PDF out.
      1. Extract original bullets from template
      2. Send to Gemini for rewriting (with validation + retry)
      3. Apply bold formatting
      4. Inject into LaTeX template
      5. Compile and return PDF
    """
    source = _get_template()
    bullets_dict = extract_bullets(source)

    markers = list(bullets_dict.keys())
    originals = list(bullets_dict.values())

    rewritten_list = rewrite_all(originals, request.quals)

    rewritten_dict = dict(zip(markers, rewritten_list))
    return _pdf_response(source, rewritten_dict)


@router.post("/scrape-job", response_model=ScrapeResponse)
async def scrape_job(request: ScrapeRequest):
    """
    Scrape job description from a URL.
    Supports common platforms: Workday, Greenhouse, SmartRecruiters, Lever, etc.

    Returns job title, description, and extracted qualifications.
    If scraping fails, returns success=False with error message.
    """
    try:
        result = await scrape_job_description(request.url)

        if result is None:
            return ScrapeResponse(
                success=False,
                url=request.url,
                error="Failed to scrape job description. The page structure may not be supported."
            )

        return ScrapeResponse(
            success=True,
            title=result.get("title"),
            description=result.get("description"),
            qualifications=result.get("qualifications"),
            platform=result.get("platform"),
            url=request.url
        )
    except Exception as e:
        return ScrapeResponse(
            success=False,
            url=request.url,
            error=f"Error scraping job: {str(e)}"
        )


@router.post("/tailor-from-url")
async def tailor_from_url(request: TailorFromUrlRequest):
    """
    Full pipeline with URL scraping support.

    Flow:
      1. If URL provided, attempt to scrape job qualifications
      2. If scraping fails or no URL provided, use manual qualifications
      3. If neither URL succeeds nor manual quals provided, return error
      4. Extract original bullets from template
      5. Send to Gemini for rewriting (with validation + retry)
      6. Apply bold formatting
      7. Inject into LaTeX template
      8. Compile and return PDF

    Request can include:
      - url: Job posting URL (optional)
      - quals: Manual qualifications (optional)

    At least one must be provided. If both provided, URL is tried first.
    """
    qualifications = None

    # Try to scrape from URL if provided
    if request.url:
        try:
            scraped = await scrape_job_description(request.url)
            if scraped and scraped.get("qualifications"):
                qualifications = scraped["qualifications"]
                # If no explicit qualifications extracted, try to parse from description
                if not qualifications and scraped.get("description"):
                    # Use description as a single qualification
                    qualifications = [scraped["description"]]
        except Exception as e:
            print(f"Error scraping job from URL: {e}")
            # Continue to try manual quals

    # Fall back to manual qualifications if scraping failed
    if not qualifications and request.quals:
        qualifications = request.quals

    # If we still don't have qualifications, return error
    if not qualifications:
        raise HTTPException(
            status_code=400,
            detail=(
                "Failed to obtain job qualifications. "
                "URL scraping failed and no manual qualifications provided. "
                "Please provide either a valid job URL or manual qualifications."
            )
        )

    # Now proceed with the standard tailor pipeline
    source = _get_template()
    bullets_dict = extract_bullets(source)

    markers = list(bullets_dict.keys())
    originals = list(bullets_dict.values())

    rewritten_list = rewrite_all(originals, qualifications)

    rewritten_dict = dict(zip(markers, rewritten_list))
    return _pdf_response(source, rewritten_dict)
