"""
Integration tests for the Skillera PDF Generator API.
"""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)

# ── Sample valid payload ──────────────────────────────────────────────

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
            "notables en adaptabilidad digital y pensamiento estrategico. Su "
            "capacidad para navegar entornos tecnologicos es superior al promedio."
        ),
        "learning_path": (
            "Se recomienda enfocarse en el desarrollo de habilidades de gestion "
            "de equipos remotos a traves de programas de coaching virtual y "
            "talleres de comunicacion asincrona."
        ),
    },
}


# ── GET endpoint tests ────────────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "pdf-generator"
        assert "timestamp" in data


class TestRootEndpoint:
    """Tests for GET /."""

    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_message(self):
        response = client.get("/")
        data = response.json()
        assert "Skillera PDF Generator" in data["message"]


# ── POST /generate-pdf tests ─────────────────────────────────────────

class TestGeneratePdfEndpoint:
    """Tests for POST /generate-pdf."""

    def test_generate_pdf_returns_200(self):
        response = client.post("/generate-pdf", json=SAMPLE_REQUEST)
        assert response.status_code == 200

    def test_generate_pdf_content_type(self):
        response = client.post("/generate-pdf", json=SAMPLE_REQUEST)
        assert response.headers["content-type"] == "application/pdf"

    def test_generate_pdf_has_filename(self):
        response = client.post("/generate-pdf", json=SAMPLE_REQUEST)
        disposition = response.headers.get("content-disposition", "")
        assert "diagnostico_" in disposition
        assert ".pdf" in disposition

    def test_generate_pdf_starts_with_pdf_header(self):
        response = client.post("/generate-pdf", json=SAMPLE_REQUEST)
        assert response.content[:5] == b"%PDF-"

    def test_generate_pdf_invalid_payload_returns_422(self):
        response = client.post("/generate-pdf", json={"user": {"name": "test"}})
        assert response.status_code == 422

    def test_generate_pdf_empty_body_returns_422(self):
        response = client.post("/generate-pdf", json={})
        assert response.status_code == 422

    def test_generate_pdf_score_out_of_range_returns_422(self):
        bad_request = json.loads(json.dumps(SAMPLE_REQUEST))
        bad_request["results"]["overall_score"] = 150  # > 100
        response = client.post("/generate-pdf", json=bad_request)
        assert response.status_code == 422


# ── POST /generate-pdf-base64 tests ──────────────────────────────────

class TestGeneratePdfBase64Endpoint:
    """Tests for POST /generate-pdf-base64."""

    def test_base64_returns_200(self):
        response = client.post("/generate-pdf-base64", json=SAMPLE_REQUEST)
        assert response.status_code == 200

    def test_base64_returns_success(self):
        response = client.post("/generate-pdf-base64", json=SAMPLE_REQUEST)
        data = response.json()
        assert data["success"] is True

    def test_base64_has_filename(self):
        response = client.post("/generate-pdf-base64", json=SAMPLE_REQUEST)
        data = response.json()
        assert "diagnostico_" in data["filename"]
        assert data["filename"].endswith(".pdf")

    def test_base64_is_valid(self):
        response = client.post("/generate-pdf-base64", json=SAMPLE_REQUEST)
        data = response.json()
        # Should decode without error
        pdf_bytes = base64.b64decode(data["pdf_base64"])
        assert pdf_bytes[:5] == b"%PDF-"

    def test_base64_invalid_payload_returns_422(self):
        response = client.post("/generate-pdf-base64", json={"bad": "data"})
        assert response.status_code == 422


# ── Edge case tests ───────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_generate_pdf_without_date(self):
        """Date should default to today when omitted."""
        request = json.loads(json.dumps(SAMPLE_REQUEST))
        request["user"]["date"] = None
        response = client.post("/generate-pdf", json=request)
        assert response.status_code == 200

    def test_generate_pdf_zero_scores(self):
        """Should handle scores of 0."""
        request = json.loads(json.dumps(SAMPLE_REQUEST))
        request["results"]["overall_score"] = 0
        for dim in request["results"]["dimensions"]:
            dim["score"] = 0
        response = client.post("/generate-pdf", json=request)
        assert response.status_code == 200

    def test_generate_pdf_max_scores(self):
        """Should handle scores of 100."""
        request = json.loads(json.dumps(SAMPLE_REQUEST))
        request["results"]["overall_score"] = 100
        for dim in request["results"]["dimensions"]:
            dim["score"] = 100
        response = client.post("/generate-pdf", json=request)
        assert response.status_code == 200
