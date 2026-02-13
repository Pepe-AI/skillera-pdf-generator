"""
Configuration settings for the PDF Generator application.
"""

import os
import json


class Config:
    """Application configuration class."""

    # Base paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    LOGO_FULL_PATH = os.path.join(ASSETS_DIR, "skillera_logo_transparente.png")

    # Load brand colors from JSON
    _colors_path = os.path.join(ASSETS_DIR, "brand_colors.json")
    with open(_colors_path, "r", encoding="utf-8") as _f:
        BRAND_COLORS = json.load(_f)

    # Convenience color references
    COLOR_PRIMARY = BRAND_COLORS["primary"]            # #6B46C1
    COLOR_SECONDARY = BRAND_COLORS["secondary"]        # #805AD5
    COLOR_BACKGROUND = BRAND_COLORS["background"]      # #1A1A2E
    COLOR_TEXT_LIGHT = BRAND_COLORS["text_light"]       # #FFFFFF
    COLOR_TEXT_DARK = BRAND_COLORS["text_dark"]         # #1A1A2E
    CHART_COLORS = BRAND_COLORS["chart_colors"]         # avanzado/intermedio/principiante

    # Gradient background colors (RGB 0-1 range)
    GRADIENT_TOP_R, GRADIENT_TOP_G, GRADIENT_TOP_B = 0.10, 0.04, 0.24
    GRADIENT_BOT_R, GRADIENT_BOT_G, GRADIENT_BOT_B = 0.18, 0.10, 0.41

    # PDF settings (A4 = 595.28 x 841.89 points)
    PDF_PAGE_WIDTH = 595.28
    PDF_PAGE_HEIGHT = 841.89
    PDF_MARGIN_LEFT = 40
    PDF_MARGIN_RIGHT = 40
    PDF_MARGIN_TOP = 40
    PDF_MARGIN_BOTTOM = 40
    PDF_CONTENT_WIDTH = PDF_PAGE_WIDTH - PDF_MARGIN_LEFT - PDF_MARGIN_RIGHT

    # Fonts
    PDF_FONT = "Helvetica"
    PDF_FONT_BOLD = "Helvetica-Bold"
    PDF_FONT_ITALIC = "Helvetica-Oblique"
    PDF_FONT_BOLD_ITALIC = "Helvetica-BoldOblique"
    PDF_FONT_SIZE_TITLE = 28
    PDF_FONT_SIZE_SUBTITLE = 14
    PDF_FONT_SIZE_BODY = 10
    PDF_FONT_SIZE_SMALL = 8

    # Chart settings
    CHART_DPI = 150
    CHART_FIGSIZE = (10, 4)

    # Branding
    SLOGAN = "Talento en transformaci\u00f3n para el futuro"

    # Section title color (cyan from reference PDF)
    COLOR_CYAN = "#38BDF8"

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        os.makedirs(cls.ASSETS_DIR, exist_ok=True)
