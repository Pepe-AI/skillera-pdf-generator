"""
Pydantic models for the IE (Inteligencia Emocional) PDF Generator.
"""

from pydantic import BaseModel, Field, field_validator


class IEUserData(BaseModel):
    """Identifying information about the assessed person."""
    name: str = Field(..., min_length=1, description="Full name")
    position: str = Field(..., min_length=1, description="Job title / position")

    @field_validator("name")
    @classmethod
    def truncate_name(cls, v: str) -> str:
        return v[:60] + "..." if len(v) > 60 else v

    @field_validator("position")
    @classmethod
    def truncate_position(cls, v: str) -> str:
        return v[:60] + "..." if len(v) > 60 else v


class IEResults(BaseModel):
    """Scoring results for the IE assessment."""
    total_score: float = Field(
        ..., ge=10, le=40,
        description="Raw score from 10 to 40 points"
    )
    nivel: str = Field(
        ..., description="Level: Bajo | Medio | Alto"
    )

    @field_validator("nivel")
    @classmethod
    def validate_nivel(cls, v: str) -> str:
        valid = {"Bajo", "Medio", "Alto"}
        if v not in valid:
            raise ValueError(f"nivel must be one of {valid}, got '{v}'")
        return v


class IEPDFRequest(BaseModel):
    """Full payload for IE PDF generation."""
    user: IEUserData
    results: IEResults


class IEPDFResponse(BaseModel):
    """Response for the IE base64 endpoint."""
    success: bool
    pdf_base64: str
    filename: str
