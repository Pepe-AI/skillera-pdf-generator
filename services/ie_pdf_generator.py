"""
IE PDF generator — PyMuPDF overlay approach.

Opens the correct reference PDF (one per nivel: Bajo/Medio/Alto) and writes
the dynamic fields (name, position, score) directly onto the page using
PyMuPDF's TextWriter.  TextWriter appends to the page content stream, so
the new text renders ON TOP of the existing design — no merge issues.

Reference PDFs: assets/Diagnostico_IE_{Bajo|Medio|Alto}_Skillera.pdf
Dimensions: 1440 x 2557.5 pt (vectorial, Poppins-Bold/Regular fonts embedded)

Field coordinates (baseline, in pt, measured with fitz.get_text("dict")):

    Nivel  | Nombre (x, y)  | Puesto (x, y)  | Score gap-center x | Score y
    -------|----------------|----------------|--------------------|---------
    Bajo   | 492, 916.5     | 478, 950.3     | 665                | 1048.1
    Medio  | 492, 940.6     | 478, 974.3     | 672                | 1129.1
    Alto   | 492, 940.6     | 478, 974.3     | 670                | 1106.7

Score gap: the template line "Tu puntuación fue:   [GAP]   puntos de un total
de 40 puntos" leaves ~93 pt of space between "fue:" and "puntos".
The score number is centered in that gap.
"""

import os
from io import BytesIO

import pymupdf

from config import Config


# ── Layout constants ──────────────────────────────────────────────────

# Coordinates per nivel: (nombre_x, nombre_y, puesto_x, puesto_y,
#                          score_gap_center_x, score_y)
_LAYOUT = {
    "Bajo":  (492.0, 916.5, 478.0, 950.3, 665.0, 1048.1),
    "Medio": (492.0, 940.6, 478.0, 974.3, 672.0, 1129.1),
    "Alto":  (492.0, 940.6, 478.0, 974.3, 670.0, 1106.7),
}

# Reference PDF filenames per nivel
_TEMPLATE_FILES = {
    "Bajo":  "Diagnostico_IE_Bajo_Skillera.pdf",
    "Medio": "Diagnostico_IE_Medio_Skillera.pdf",
    "Alto":  "Diagnostico_IE_Alto_Skillera.pdf",
}

# Text colors
_WHITE = (1.0, 1.0, 1.0)

# Font sizes matching the original Poppins fonts in the reference PDFs
_SIZE_LABEL = 25.0   # Poppins-Bold 25 pt → use Gotham-Bold 25 pt
_SIZE_SCORE = 28.0   # Poppins-Regular 28 pt → use Gotham-Book 28 pt

# Max pixel width for name / position before truncation
_MAX_TEXT_WIDTH = 700.0


class IEPDFGenerator:
    """
    Fills dynamic user data into Inteligencia Emocional reference PDFs.

    Selects the template for the user's nivel (Bajo/Medio/Alto) and
    overlays name, position, and total score at their design positions.
    """

    def __init__(self):
        self._font_bold = pymupdf.Font(fontfile=Config.GOTHAM_BOLD)
        self._font_book = pymupdf.Font(fontfile=Config.GOTHAM_BOOK)

        assets = Config.ASSETS_DIR
        self._templates = {
            nivel: os.path.join(assets, fname)
            for nivel, fname in _TEMPLATE_FILES.items()
        }

    # ── Public API ────────────────────────────────────────────────────

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Generate an IE diagnostic PDF for the given user data.

        Args:
            data: dict with keys:
                user:    { name: str, position: str }
                results: { total_score: float, nivel: str }

        Returns:
            BytesIO containing the completed PDF.
        """
        user = data["user"]
        results = data["results"]
        nivel = results["nivel"]
        total_score = int(results["total_score"])

        nombre_x, nombre_y, puesto_x, puesto_y, score_cx, score_y = _LAYOUT[nivel]

        doc = pymupdf.open(self._templates[nivel])
        page = doc[0]

        self._write_name(page, nombre_x, nombre_y, user["name"])
        self._write_position(page, puesto_x, puesto_y, user["position"])
        self._write_score(page, score_cx, score_y, total_score)

        buf = BytesIO()
        doc.save(buf)
        doc.close()
        buf.seek(0)
        return buf

    # ── Private helpers ───────────────────────────────────────────────

    def _write_name(self, page, x: float, y: float, name: str):
        """Write user name in Gotham-Bold 25 pt white."""
        text = self._fit_text(name, self._font_bold, _SIZE_LABEL, _MAX_TEXT_WIDTH)
        self._put(page, x, y, text, self._font_bold, _SIZE_LABEL)

    def _write_position(self, page, x: float, y: float, position: str):
        """Write job position in Gotham-Book 25 pt white."""
        text = self._fit_text(position, self._font_book, _SIZE_LABEL, _MAX_TEXT_WIDTH)
        self._put(page, x, y, text, self._font_book, _SIZE_LABEL)

    def _write_score(self, page, gap_center_x: float, y: float, score: int):
        """Write score number centered inside the template gap."""
        score_str = str(score)
        score_w = self._font_bold.text_length(score_str, fontsize=_SIZE_SCORE)
        x = gap_center_x - score_w / 2
        self._put(page, x, y, score_str, self._font_bold, _SIZE_SCORE)

    @staticmethod
    def _fit_text(text: str, font, size: float, max_width: float) -> str:
        """Truncate text with '...' if it exceeds max_width at the given size."""
        if font.text_length(text, fontsize=size) <= max_width:
            return text
        while len(text) > 1:
            text = text[:-1]
            if font.text_length(text + "...", fontsize=size) <= max_width:
                return text + "..."
        return text

    @staticmethod
    def _put(page, x: float, y: float, text: str, font, size: float):
        """Append text at (x, y) baseline using TextWriter (renders on top)."""
        if not text:
            return
        writer = pymupdf.TextWriter(page.rect)
        writer.append(pymupdf.Point(x, y), text, font=font, fontsize=size)
        writer.write_text(page, color=_WHITE)
