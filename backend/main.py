"""
main.py — FastAPI application.

Endpoints:
  GET  /bullets        → returns { marker_id: original_text } for the AI
  POST /generate-pdf   → receives rewritten bullets, returns compiled PDF
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from latex_parser import extract_bullets, load_template
from latex_injector import inject_bullets
from pdf_compiler import compile_pdf, CompilationError
from models import BulletsPayload, BulletsResponse

app = FastAPI(title="Resume Tailoring API")


def _get_template() -> str:
    try:
        return load_template()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Template not found: {e}")


@app.get("/bullets", response_model=BulletsResponse)
def get_bullets():
    """
    Returns the original bullet text for every <<BULLET_*>> marker
    in the template. This is the payload the AI service receives to rewrite.
    """
    source = _get_template()
    return BulletsResponse(bullets=extract_bullets(source))


@app.post("/generate-pdf")
def generate_pdf(payload: BulletsPayload):
    """
    Accepts a dict of { marker_id: rewritten_plain_text }, injects into
    the LaTeX template with bold post-processing, compiles to PDF, and
    returns the PDF binary.
    """
    source = _get_template()

    try:
        final_tex = inject_bullets(source, payload.bullets)
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
