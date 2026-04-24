"""
Pydantic models for the AT (Alfabetización Tecnológica) PDF Generator.
"""

from pydantic import BaseModel, Field, field_validator


class ATUserData(BaseModel):
    """Identifying information about the assessed person."""
    name: str = Field(..., min_length=1, description="Full name")

    @field_validator("name")
    @classmethod
    def truncate_name(cls, v: str) -> str:
        return v[:60] + "..." if len(v) > 60 else v


class ATResults(BaseModel):
    """Scoring results for the AT assessment."""
    total_score: int = Field(
        ..., ge=10, le=30,
        description="Raw score from 10 to 30 points"
    )
    nivel: str = Field(
        ..., description="Level: Básico | Intermedio | Avanzado"
    )

    @field_validator("nivel")
    @classmethod
    def validate_nivel(cls, v: str) -> str:
        valid = {"Básico", "Intermedio", "Avanzado"}
        if v not in valid:
            raise ValueError(f"nivel must be one of {valid}, got '{v}'")
        return v


class ATPDFRequest(BaseModel):
    """Full payload for AT PDF generation."""
    user: ATUserData
    results: ATResults


class ATPDFResponse(BaseModel):
    """Response for the AT base64 endpoint."""
    success: bool
    pdf_base64: str
    filename: str
