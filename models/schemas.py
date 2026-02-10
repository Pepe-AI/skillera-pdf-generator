"""
Pydantic models for the PDF Generator API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class DimensionScore(BaseModel):
    """A single dimension with its name and numeric score."""
    name: str = Field(..., description="Dimension name, e.g. 'Pensamiento Estratégico'")
    score: float = Field(..., ge=0, le=100, description="Score from 0 to 100")


class DimensionLevel(BaseModel):
    """A dimension with its assigned level label."""
    name: str = Field(..., description="Dimension name")
    level: str = Field(..., description="One of: Avanzado, Intermedio, Principiante")


class UserData(BaseModel):
    """Identifying information about the assessed person."""
    name: str = Field(..., min_length=1, description="Full name")
    position: str = Field(..., min_length=1, description="Job title / position")
    date: Optional[str] = Field(None, description="Assessment date, e.g. '2025-06-15'. Defaults to today.")


class Results(BaseModel):
    """Overall result plus per-dimension breakdown."""
    overall_level: str = Field(..., description="General level: Avanzado | Intermedio | Principiante")
    overall_score: float = Field(..., ge=0, le=100, description="General score 0-100")
    dimensions: list[DimensionScore] = Field(..., min_length=1, description="List of dimension scores")
    dimension_levels: list[DimensionLevel] = Field(..., min_length=1, description="Level per dimension")


class AIContent(BaseModel):
    """AI-generated text blocks for the report."""
    summary: str = Field(..., min_length=10, description="Executive summary paragraph")
    learning_path: str = Field(..., min_length=10, description="Recommended learning path paragraph")


class PDFRequest(BaseModel):
    """Full payload for PDF generation."""
    user: UserData
    results: Results
    ai_content: AIContent


class PDFResponse(BaseModel):
    """Response for the base64 endpoint."""
    success: bool
    pdf_base64: str
    filename: str
