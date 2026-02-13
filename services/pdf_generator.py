"""
PDF generation service — template-based approach.

Opens the branded PDF template (assets/template.pdf) which already contains
the full visual design (gradient, banner, logo, section titles, chart axes).
Then overlays dynamic data: user info, scores, summary, chart bars, and
learning path text.
"""

from io import BytesIO
from datetime import date

import pymupdf  # PyMuPDF

from config import Config


# ── Color helpers ────────────────────────────────────────────────────

# Template background color (used to "erase" bar areas before redrawing)
_BG_RGB = (0.1373, 0.0510, 0.3098)  # dark purple from template bg

# Text colors
_WHITE = (1.0, 1.0, 1.0)
_LIGHT = (0.957, 0.941, 0.976)       # #F4F0F9 — label color in template
_CYAN = (0.396, 0.651, 0.980)        # #65A6FA — section title color

# Chart bar colors (matching template legend)
_BAR_COLORS = {
    "Avanzado":     (0.635, 0.169, 1.0),     # purple  #A22BFF
    "Intermedio":   (0.286, 0.765, 0.984),    # cyan    #49C3FB
    "Principiante": (0.396, 0.651, 0.980),    # blue    #65A6FA
}


class PDFGenerator:
    """Generates leadership diagnostic PDFs by filling a branded template."""

    def __init__(self):
        """Initialize with template path."""
        self.template_path = Config.TEMPLATE_PDF_PATH

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Generate the full leadership diagnostic PDF.

        Args:
            data: Dict with keys: user, results, ai_content

        Returns:
            BytesIO containing the completed PDF.
        """
        doc = pymupdf.open(self.template_path)
        page = doc[0]
        page_h = page.rect.height  # 842.25

        user = data["user"]
        results = data["results"]
        ai = data["ai_content"]

        # ── 1. User data fields ──────────────────────────────────────
        self._fill_user_data(page, user)

        # ── 2. Result fields ─────────────────────────────────────────
        self._fill_results(page, results)

        # ── 3. Summary text ──────────────────────────────────────────
        self._fill_summary(page, ai.get("summary", ""))

        # ── 4. Chart bars ────────────────────────────────────────────
        self._fill_chart_bars(page, results)

        # ── 5. Learning path ─────────────────────────────────────────
        self._fill_learning_path(page, ai.get("learning_path", ""))

        # Export
        buffer = BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        return buffer

    # ── User data ────────────────────────────────────────────────────

    def _fill_user_data(self, page, user: dict):
        """Fill name, position, and date fields.

        Template label positions (PyMuPDF coords, y from top):
        - "Elaborado para:" → x0=28.7, x1=158.2, y_bottom=228.6
        - "Puesto/Rol:"     → x0=270.6, x1=372.4, y_bottom=228.6
        - "Fecha de Emisión:" → x0=28.7, x1=175.5, y_bottom=245.1
        """
        name = user.get("name", "")
        position = user.get("position", "")
        display_date = user.get("date") or date.today().isoformat()

        # Name — after "Elaborado para:" (x1=158.2), baseline at y_bottom=228
        self._insert_text(page, 160, 226, name,
                          fontsize=12, color=_LIGHT, italic=True)

        # Position — after "Puesto/Rol:" (x1=372.4)
        self._insert_text(page, 374, 226, position,
                          fontsize=12, color=_LIGHT, bold=True)

        # Date — after "Fecha de Emisión:" (x1=175.5)
        self._insert_text(page, 177, 243, display_date,
                          fontsize=12, color=_LIGHT, bold=True)

    # ── Results ──────────────────────────────────────────────────────

    def _fill_results(self, page, results: dict):
        """Fill overall level and score."""
        level = results.get("overall_level", "")
        score = results.get("overall_score", 0)

        num_dims = len(results.get("dimensions", []))
        max_per_dim = 35
        max_score = num_dims * max_per_dim if num_dims > 0 else 140

        # "Tu Resultado General:" x1=218.9, y_bottom=280.8
        self._insert_text(page, 221, 279, level.upper(),
                          fontsize=13, color=_CYAN, bold=True)

        # "Puntuación Global:" x1=192.1, y_bottom=302.6
        score_text = f"{score:.0f}/ {max_score}"
        self._insert_text(page, 194, 301, score_text,
                          fontsize=13, color=_WHITE, bold=True)

    # ── Summary ──────────────────────────────────────────────────────

    def _fill_summary(self, page, summary: str):
        """Fill the summary paragraph below the score."""
        if not summary:
            return

        # Clean HTML tags for plain text
        clean = self._strip_html(summary)

        # Summary area: x=26 to 559, y starts at ~312 (842-530)
        # Using a text writer for word-wrapped text
        rect = pymupdf.Rect(27, 312, 559, 430)
        self._insert_paragraph(page, rect, clean,
                               fontsize=10, color=_WHITE)

    # ── Chart bars ───────────────────────────────────────────────────

    def _fill_chart_bars(self, page, results: dict):
        """Draw horizontal bars for each dimension score.

        Template chart area (PyMuPDF coords, Y from top):
        - Chart left edge (0 score): x = 212.3
        - Chart right edge (35 score): x = 512.4
        - Bar rows (4 bars, measured from template eraser rects):
            Row 0: y = 441.2 to 471.8  (I. Liderazgo e Influencia Social)
            Row 1: y = 475.2 to 505.8  (II. Empatía y Escucha Activa)
            Row 2: y = 509.2 to 539.9  (III. Delegación y Desarrollo del Talento)
            Row 3: y = 543.3 to 573.9  (IV. Resiliencia y Adaptabilidad)
        """
        dimensions = results.get("dimensions", [])
        dim_levels = results.get("dimension_levels", [])

        chart_x0 = 212.3   # x where score=0
        chart_x35 = 512.4  # x where score=35
        px_per_unit = (chart_x35 - chart_x0) / 35.0  # ~8.57 px per score unit

        # Y positions for each bar row (PyMuPDF coords, Y from top of page)
        bar_rows = [
            (441.2, 471.8),  # Row 0 — I. Liderazgo e Influencia Social
            (475.2, 505.8),  # Row 1 — II. Empatía y Escucha Activa
            (509.2, 539.9),  # Row 2 — III. Delegación y Desarrollo del Talento
            (543.3, 573.9),  # Row 3 — IV. Resiliencia y Adaptabilidad
        ]

        for i, dim in enumerate(dimensions):
            if i >= len(bar_rows):
                break

            score = dim.get("score", 0) if isinstance(dim, dict) else dim.score
            level = "Intermedio"
            if i < len(dim_levels):
                lv = dim_levels[i]
                level = lv.get("level", "Intermedio") if isinstance(lv, dict) else lv.level

            # Bar color based on level
            bar_color = _BAR_COLORS.get(level, _BAR_COLORS["Intermedio"])

            # Calculate bar width
            bar_width = score * px_per_unit
            y_top, y_bottom = bar_rows[i]

            # Erase existing bar (draw bg-colored rect over it)
            erase_rect = pymupdf.Rect(chart_x0, y_top, chart_x35 + 5, y_bottom)
            page.draw_rect(erase_rect, color=None, fill=_BG_RGB)

            # Draw new bar
            if bar_width > 0:
                bar_rect = pymupdf.Rect(
                    chart_x0, y_top,
                    chart_x0 + bar_width, y_bottom,
                )
                page.draw_rect(bar_rect, color=None, fill=bar_color)

    # ── Learning path ────────────────────────────────────────────────

    def _fill_learning_path(self, page, learning_path: str):
        """Fill the learning path text below its title."""
        if not learning_path:
            return

        clean = self._strip_html(learning_path)

        # "Ruta de Aprendizaje Recomendada" title is at y≈600 (842-242)
        # Text area starts below it: y≈615 to bottom of page (~820)
        rect = pymupdf.Rect(27, 612, 559, 820)
        self._insert_paragraph(page, rect, clean,
                               fontsize=10, color=_WHITE)

    # ── Helper methods ───────────────────────────────────────────────

    def _insert_text(self, page, x: float, y: float, text: str,
                     fontsize: float = 11, color=_WHITE,
                     bold: bool = False, italic: bool = False):
        """Insert a single line of text at the given position."""
        if not text:
            return

        fontname = "helv"
        if bold and italic:
            fontname = "hebi"
        elif bold:
            fontname = "hebo"
        elif italic:
            fontname = "heit"

        page.insert_text(
            pymupdf.Point(x, y),
            text,
            fontsize=fontsize,
            fontname=fontname,
            color=color,
        )

    def _insert_paragraph(self, page, rect: pymupdf.Rect, text: str,
                          fontsize: float = 10, color=_WHITE):
        """Insert word-wrapped text inside a rectangle."""
        # Use insert_textbox for automatic word wrapping
        page.insert_textbox(
            rect,
            text,
            fontsize=fontsize,
            fontname="helv",
            color=color,
            align=pymupdf.TEXT_ALIGN_JUSTIFY,
        )

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text, keeping plain content."""
        import re
        # Replace <br/> and <br> with newlines
        text = re.sub(r'<br\s*/?>', '\n', text)
        # Remove all other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
