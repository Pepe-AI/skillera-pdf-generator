"""Skillera PDF Generator API."""

import base64
from datetime import datetime, date
from io import BytesIO

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import PDFRequest, PDFResponse
from services.pdf_generator import PDFGenerator


app = FastAPI(
    title="Skillera PDF Generator",
    version="1.0.0",
    description="API para generar reportes PDF de diagnosticos de liderazgo",
)

# Instantiate generator once (stateless, reusable)
pdf_generator = PDFGenerator()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "pdf-generator",
    }


@app.get("/")
def root():
    """Root endpoint with service info."""
    return {"message": "Skillera PDF Generator API"}


@app.post("/generate-pdf")
def generate_pdf(request: PDFRequest):
    """Generate PDF and return as a downloadable binary file."""
    try:
        pdf_buffer: BytesIO = pdf_generator.generate_pdf(request.model_dump())

        filename = (
            f"diagnostico_{request.user.name.replace(' ', '_')}"
            f"_{date.today().isoformat()}.pdf"
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.post("/generate-pdf-base64", response_model=PDFResponse)
def generate_pdf_base64(request: PDFRequest):
    """Generate PDF and return as base64 string (for WhatsApp/Email integration)."""
    try:
        pdf_buffer: BytesIO = pdf_generator.generate_pdf(request.model_dump())

        pdf_bytes = pdf_buffer.read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        filename = (
            f"diagnostico_{request.user.name.replace(' ', '_')}"
            f"_{date.today().isoformat()}.pdf"
        )

        return PDFResponse(
            success=True,
            pdf_base64=pdf_b64,
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
