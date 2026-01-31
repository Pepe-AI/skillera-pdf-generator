"""
Configuration settings for the PDF Generator application.
"""

import os


class Config:
    """Application configuration class."""
    
    # Base paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    
    # PDF settings
    PDF_PAGE_SIZE = "A4"
    PDF_FONT = "Helvetica"
    PDF_FONT_SIZE = 12
    
    # Chart settings
    CHART_DPI = 100
    CHART_FIGSIZE = (8, 6)
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        os.makedirs(cls.ASSETS_DIR, exist_ok=True)
