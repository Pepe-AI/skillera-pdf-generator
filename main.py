"""Skillera PDF Generator API."""

import base64
import os
from datetime import datetime, date
from io import BytesIO

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, Response

from models.schemas import PDFRequest, PDFResponse
from services.pdf_generator import PDFGenerator
from services.pdf_store import PDFStore


app = FastAPI(
    title="Skillera PDF Generator",
    version="1.1.0",
    description="API para generar reportes PDF de diagnosticos de liderazgo",
)

# ── Singleton instances ───────────────────────────────────────────────

pdf_generator = PDFGenerator()

# TTL configurable via environment variable (default: 30 minutes)
PDF_TTL_MINUTES = int(os.getenv("PDF_TTL_MINUTES", "30"))
PDF_MAX_ITEMS = int(os.getenv("PDF_MAX_ITEMS", "100"))

pdf_store = PDFStore(ttl_minutes=PDF_TTL_MINUTES, max_items=PDF_MAX_ITEMS)


# ── Helper: build filename ────────────────────────────────────────────

def _build_filename(user_name: str) -> str:
    """Generate a consistent filename from the user's name."""
    safe_name = user_name.replace(" ", "_")
    return f"diagnostico_{safe_name}_{date.today().isoformat()}.pdf"


# ── Helper: build public URL ──────────────────────────────────────────

def _build_pdf_url(request: Request, pdf_id: str) -> str:
    """
    Build the full public URL for a stored PDF.

    Uses the X-Forwarded-Host / X-Forwarded-Proto headers if behind
    a reverse proxy (Render), otherwise falls back to request.base_url.

    Can be overridden entirely via the PDF_BASE_URL env var.
    Example: PDF_BASE_URL=https://skillera-pdf-generator.onrender.com
    """
    base = os.getenv("PDF_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/pdfs/{pdf_id}"

    # Build from request (works behind Render's proxy)
    return f"{request.base_url}pdfs/{pdf_id}"


# ── GET endpoints ─────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "pdf-generator",
        "pdf_store_count": pdf_store.count,
        "pdf_ttl_minutes": PDF_TTL_MINUTES,
    }


@app.get("/")
def root():
    """Root endpoint with service info."""
    return {"message": "Skillera PDF Generator API v1.1.0"}


# ── POST /generate-pdf (binary download) ─────────────────────────────

@app.post("/generate-pdf")
def generate_pdf(request: PDFRequest):
    """Generate PDF and return as a downloadable binary file."""
    try:
        pdf_buffer: BytesIO = pdf_generator.generate_pdf(request.model_dump())
        filename = _build_filename(request.user.name)

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ── POST /generate-pdf-base64 (base64 string) ────────────────────────

@app.post("/generate-pdf-base64", response_model=PDFResponse)
def generate_pdf_base64(request: PDFRequest):
    """Generate PDF and return as base64 string (for WhatsApp/Email integration)."""
    try:
        pdf_buffer: BytesIO = pdf_generator.generate_pdf(request.model_dump())
        pdf_bytes = pdf_buffer.read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        filename = _build_filename(request.user.name)

        return PDFResponse(
            success=True,
            pdf_base64=pdf_b64,
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ── POST /generate-pdf-url (NEW: returns public URL) ─────────────────

@app.post("/generate-pdf-url")
def generate_pdf_url(request: PDFRequest, req: Request):
    """
    Generate PDF, store it temporarily, and return a public URL.

    This is the endpoint that n8n should call. The returned URL can be
    passed to Kommo Salesbot to send the PDF via WhatsApp template.

    Response:
        {
            "success": true,
            "pdf_url": "https://skillera-pdf-generator.onrender.com/pdfs/{uuid}",
            "filename": "diagnostico_Maria_Garcia_2025-06-15.pdf",
            "expires_in_minutes": 30
        }
    """
    try:
        # 1. Generate the PDF
        pdf_buffer: BytesIO = pdf_generator.generate_pdf(request.model_dump())
        pdf_bytes = pdf_buffer.read()
        filename = _build_filename(request.user.name)

        # 2. Store in memory with TTL
        pdf_id = pdf_store.save(pdf_bytes, filename)

        # 3. Build public URL
        pdf_url = _build_pdf_url(req, pdf_id)

        return {
            "success": True,
            "pdf_url": pdf_url,
            "pdf_id": pdf_id,
            "filename": filename,
            "expires_in_minutes": PDF_TTL_MINUTES,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ── GET /pdfs/{pdf_id} (serve stored PDF) ─────────────────────────────

@app.get("/pdfs/{pdf_id}")
def get_stored_pdf(pdf_id: str):
    """
    Serve a previously generated PDF by its UUID.

    This URL is what WhatsApp / Kommo Salesbot will use to download
    the PDF for the document header in the WA template.

    Returns 404 if the PDF has expired or doesn't exist.
    """
    entry = pdf_store.get(pdf_id)

    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="PDF not found or expired. PDFs are available for "
                   f"{PDF_TTL_MINUTES} minutes after generation.",
        )

    return Response(
        content=entry["bytes"],
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{entry["filename"]}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


# ── DELETE /pdfs/{pdf_id} (manual cleanup) ────────────────────────────

@app.delete("/pdfs/{pdf_id}")
def delete_stored_pdf(pdf_id: str):
    """
    Manually delete a stored PDF (called by n8n after delivery).

    This is optional — PDFs auto-expire after TTL. But calling this
    immediately after successful WhatsApp delivery frees memory sooner.
    """
    deleted = pdf_store.delete(pdf_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="PDF not found or already expired.")

    return {"success": True, "message": "PDF deleted successfully."}


# ── GET /pdfs (admin: list stored PDFs) ───────────────────────────────

@app.get("/pdfs")
def list_stored_pdfs():
    """
    List currently stored PDFs (for debugging / monitoring).
    Does NOT return the PDF bytes, just metadata.
    """
    return {
        "count": pdf_store.count,
        "ttl_minutes": PDF_TTL_MINUTES,
        "max_items": PDF_MAX_ITEMS,
    }