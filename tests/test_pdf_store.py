"""
Tests for the PDF URL generation and temporary storage endpoints.
"""

import json
import pytest
from fastapi.testclient import TestClient

from main import app, pdf_store


client = TestClient(app)

# ── Sample payload (same as test_endpoints.py) ────────────────────────

SAMPLE_REQUEST = {
    "user": {
        "name": "Maria Garcia Lopez",
        "position": "Directora de Innovacion",
        "date": "2025-06-15",
    },
    "results": {
        "overall_level": "Intermedio",
        "overall_score": 67.5,
        "dimensions": [
            {"name": "Pensamiento Estrategico", "score": 75},
            {"name": "Influencia y Comunicacion", "score": 60},
            {"name": "Adaptabilidad Digital", "score": 82},
            {"name": "Gestion de Equipos Remotos", "score": 53},
        ],
        "dimension_levels": [
            {"name": "Pensamiento Estrategico", "level": "Avanzado"},
            {"name": "Influencia y Comunicacion", "level": "Intermedio"},
            {"name": "Adaptabilidad Digital", "level": "Avanzado"},
            {"name": "Gestion de Equipos Remotos", "level": "Principiante"},
        ],
    },
    "ai_content": {
        "summary": (
            "Maria demuestra un perfil de liderazgo intermedio con fortalezas "
            "notables en adaptabilidad digital y pensamiento estrategico."
        ),
        "learning_path": (
            "Se recomienda enfocarse en el desarrollo de habilidades de gestion "
            "de equipos remotos a traves de programas de coaching virtual."
        ),
    },
}


# ── POST /generate-pdf-url tests ─────────────────────────────────────

class TestGeneratePdfUrl:
    """Tests for POST /generate-pdf-url."""

    def test_returns_200(self):
        response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        assert response.status_code == 200

    def test_returns_success_true(self):
        response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        data = response.json()
        assert data["success"] is True

    def test_returns_pdf_url(self):
        response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        data = response.json()
        assert "/pdfs/" in data["pdf_url"]

    def test_returns_pdf_id(self):
        response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        data = response.json()
        assert len(data["pdf_id"]) == 36  # UUID format

    def test_returns_filename(self):
        response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        data = response.json()
        assert "diagnostico_" in data["filename"]
        assert data["filename"].endswith(".pdf")

    def test_returns_expires_in_minutes(self):
        response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        data = response.json()
        assert data["expires_in_minutes"] > 0

    def test_invalid_payload_returns_422(self):
        response = client.post("/generate-pdf-url", json={"bad": "data"})
        assert response.status_code == 422


# ── GET /pdfs/{pdf_id} tests ─────────────────────────────────────────

class TestGetStoredPdf:
    """Tests for GET /pdfs/{pdf_id}."""

    def test_retrieve_stored_pdf(self):
        """Generate a PDF URL, then retrieve it."""
        # Step 1: Generate
        gen_response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        pdf_id = gen_response.json()["pdf_id"]

        # Step 2: Retrieve
        get_response = client.get(f"/pdfs/{pdf_id}")
        assert get_response.status_code == 200
        assert get_response.headers["content-type"] == "application/pdf"
        assert get_response.content[:5] == b"%PDF-"

    def test_retrieve_has_filename_header(self):
        gen_response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        pdf_id = gen_response.json()["pdf_id"]

        get_response = client.get(f"/pdfs/{pdf_id}")
        disposition = get_response.headers.get("content-disposition", "")
        assert "diagnostico_" in disposition

    def test_nonexistent_pdf_returns_404(self):
        response = client.get("/pdfs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_invalid_uuid_returns_404(self):
        response = client.get("/pdfs/not-a-valid-uuid")
        assert response.status_code == 404

    def test_multiple_pdfs_independent(self):
        """Each generation creates a unique URL."""
        resp1 = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        resp2 = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)

        id1 = resp1.json()["pdf_id"]
        id2 = resp2.json()["pdf_id"]

        assert id1 != id2

        # Both should be retrievable
        assert client.get(f"/pdfs/{id1}").status_code == 200
        assert client.get(f"/pdfs/{id2}").status_code == 200


# ── DELETE /pdfs/{pdf_id} tests ───────────────────────────────────────

class TestDeleteStoredPdf:
    """Tests for DELETE /pdfs/{pdf_id}."""

    def test_delete_existing_pdf(self):
        gen_response = client.post("/generate-pdf-url", json=SAMPLE_REQUEST)
        pdf_id = gen_response.json()["pdf_id"]

        # Delete
        del_response = client.delete(f"/pdfs/{pdf_id}")
        assert del_response.status_code == 200
        assert del_response.json()["success"] is True

        # Should no longer be retrievable
        get_response = client.get(f"/pdfs/{pdf_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        response = client.delete("/pdfs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


# ── GET /pdfs (list) tests ────────────────────────────────────────────

class TestListStoredPdfs:
    """Tests for GET /pdfs."""

    def test_list_returns_count(self):
        response = client.get("/pdfs")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "ttl_minutes" in data


# ── Health endpoint includes store info ───────────────────────────────

class TestHealthWithStore:
    """Test that health endpoint reports store status."""

    def test_health_includes_store_count(self):
        response = client.get("/health")
        data = response.json()
        assert "pdf_store_count" in data
        assert "pdf_ttl_minutes" in data