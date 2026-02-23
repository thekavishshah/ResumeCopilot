from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.latex.parser import extract_bullets, load_template
from app.latex.injector import inject_bullets
from app.latex.compiler import compile_pdf, CompilationError
from app.ai.rewriter import rewrite_all
from app.models import BulletsPayload, BulletsResponse, TailorRequest

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
