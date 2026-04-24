"""
AT PDF generator — PyMuPDF overlay approach.

Opens the correct reference PDF (one per nivel: Básico/Intermedio/Avanzado)
and writes the dynamic fields (name, score) directly onto the page using
PyMuPDF's page.insert_text().

Reference PDFs: assets/Diagnostico_AT_{Basico|Intermedio|Avanzado}_Skillera.pdf
Dimensions: 1440 x 2557.5 pt (vectorial, Poppins fonts embedded)

Field coordinates (baseline, in pt, measured with fitz.get_text("dict")):

    Nivel       | Nombre (x, y)  | Score gap-center x | Score y
    ------------|----------------|--------------------|---------
    Básico      | 492.7, 949.3   | 687                | 1135.9
    Intermedio  | 504.5, 941.7   | 678                | 1105.8
    Avanzado    | 492.7, 949.3   | 678                | 1138.9

Score gap: the template line "Tu puntuación fue:   [GAP]   puntos de un total
de 30 puntos" leaves whitespace.  The score number is centered in that gap.
"""

import os
from io import BytesIO

import pymupdf

from config import Config


# ── Layout constants ──────────────────────────────────────────────────

# Coordinates per nivel: (nombre_x, nombre_y, score_gap_center_x, score_y)
_LAYOUT = {
    "Básico":      (492.7, 942.0, 687.0, 1128.0),
    "Intermedio":  (504.5, 934.0, 678.0, 1098.0),
    "Avanzado":    (492.7, 942.0, 678.0, 1131.0),
}

# Reference PDF filenames per nivel
_TEMPLATE_FILES = {
    "Básico":      "Diagnostico_AT_Basico_Skillera.pdf",
    "Intermedio":  "Diagnostico_AT_Intermedio_Skillera.pdf",
    "Avanzado":    "Diagnostico_AT_Avanzado_Skillera.pdf",
}

# Text color: white
_WHITE = (1.0, 1.0, 1.0)

# Rasterization DPI — templates are pre-rasterized once at startup
_RASTER_DPI = 72
_JPEG_QUALITY = 85

# Font sizes matching the original Poppins fonts in the reference PDFs
_SIZE_NAME  = 25.0   # Nombre — Poppins-Bold 25 pt → Montserrat-Light
_SIZE_SCORE = 28.0   # Score  — Poppins-Bold 28 pt → Montserrat-Bold

# Unique internal font names (distinct from IE to avoid conflicts)
_FNAME_BOLD  = "at_bold"
_FNAME_LIGHT = "at_light"

# Max width (pt) for name before truncation
_MAX_TEXT_WIDTH = 700.0


class ATPDFGenerator:
    """
    Fills dynamic user data into Alfabetización Tecnológica reference PDFs.

    Selects the template for the user's nivel (Básico/Intermedio/Avanzado)
    and overlays name and total score at their design positions.
    """

    def __init__(self):
        # Font objects used ONLY for text-width measurement (not for rendering)
        self._measure_bold  = pymupdf.Font(fontfile=Config.FONT_BOLD)
        self._measure_light = pymupdf.Font(fontfile=Config.FONT_LIGHT)

        # Pre-rasterize templates once at startup
        # Cached data per nivel: (jpeg_bytes, page_width, page_height)
        self._cached_bg: dict[str, tuple[bytes, float, float]] = {}
        assets = Config.ASSETS_DIR
        for nivel, fname in _TEMPLATE_FILES.items():
            path = os.path.join(assets, fname)
            doc = pymupdf.open(path)
            page = doc[0]
            pw, ph = page.rect.width, page.rect.height
            pix = page.get_pixmap(dpi=_RASTER_DPI)
            self._cached_bg[nivel] = (pix.tobytes("jpeg", _JPEG_QUALITY), pw, ph)
            doc.close()

    # ── Public API ────────────────────────────────────────────────────

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Generate an AT diagnostic PDF for the given user data.

        Args:
            data: dict with keys:
                user:    { name: str }
                results: { total_score: int, nivel: str }

        Returns:
            BytesIO containing the completed PDF.
        """
        user = data["user"]
        results = data["results"]
        nivel = results["nivel"]
        total_score = int(results["total_score"])

        nombre_x, nombre_y, score_cx, score_y = _LAYOUT[nivel]

        # Use pre-rasterized JPEG from cache
        img_bytes, page_w, page_h = self._cached_bg[nivel]
        doc = pymupdf.open()
        page = doc.new_page(width=page_w, height=page_h)
        page.insert_image(page.rect, stream=img_bytes)

        # Overlay dynamic text
        self._write_name(page, nombre_x, nombre_y, user["name"])
        self._write_score(page, score_cx, score_y, total_score)

        buf = BytesIO()
        doc.save(buf, deflate=True, garbage=4, clean=False, pretty=False)
        doc.close()
        buf.seek(0)
        return buf

    # ── Private helpers ───────────────────────────────────────────────

    def _write_name(self, page, x: float, y: float, name: str):
        """Write user name in Montserrat-Light 25 pt white."""
        text = self._fit_text(name, self._measure_light, _SIZE_NAME, _MAX_TEXT_WIDTH)
        self._put(page, x, y, text, Config.FONT_LIGHT, _FNAME_LIGHT, _SIZE_NAME)

    def _write_score(self, page, gap_center_x: float, y: float, score: int):
        """Write score number centered inside the template gap."""
        score_str = str(score)
        score_w = self._measure_bold.text_length(score_str, fontsize=_SIZE_SCORE)
        x = gap_center_x - score_w / 2
        self._put(page, x, y, score_str, Config.FONT_BOLD, _FNAME_BOLD, _SIZE_SCORE)

    @staticmethod
    def _fit_text(text: str, font: pymupdf.Font, size: float, max_width: float) -> str:
        """Truncate text with '...' if it exceeds max_width at the given size."""
        if font.text_length(text, fontsize=size) <= max_width:
            return text
        while len(text) > 1:
            text = text[:-1]
            if font.text_length(text + "...", fontsize=size) <= max_width:
                return text + "..."
        return text

    @staticmethod
    def _put(page, x: float, y: float, text: str,
             fontfile: str, fontname: str, size: float):
        """Insert text at (x, y) baseline using page.insert_text()."""
        if not text:
            return
        page.insert_text(
            pymupdf.Point(x, y),
            text,
            fontfile=fontfile,
            fontname=fontname,
            fontsize=size,
            color=_WHITE,
        )
