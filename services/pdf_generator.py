"""
PDF generation service — template-based approach.

Opens the branded PDF template (assets/template.pdf) which already contains
the full visual design (gradient, banner, logo, section titles, chart axes).
Then overlays dynamic data: user info, scores, summary, chart bars, and
learning path text.

Fonts: Montserrat (Bold, BoldItalic, Light) — visual match for Gotham.
"""

from io import BytesIO
from datetime import date
import re
import os

import pymupdf  # PyMuPDF

from config import Config


# ── Color helpers ────────────────────────────────────────────────────

# Template background color (used to "erase" bar areas before redrawing)
_BG_RGB = (0.1373, 0.0510, 0.3098)  # dark purple from template bg

# Text colors (from design JSON)
_WHITE = (1.0, 1.0, 1.0)                    # #FFFFFF
_LIGHT = (0.957, 0.941, 0.976)              # #F4F0F9
_CYAN = (0.396, 0.651, 0.980)              # #65A6FA

# Chart bar colors (matching template legend)
_BAR_COLORS = {
    "Avanzado":     (0.635, 0.169, 1.0),     # purple  #A22BFF
    "Intermedio":   (0.286, 0.765, 0.984),    # cyan    #49C3FB
    "Principiante": (0.396, 0.651, 0.980),    # blue    #65A6FA
}


class PDFGenerator:
    """Generates leadership diagnostic PDFs by filling a branded template."""

    def __init__(self):
        """Initialize with template path and load custom fonts."""
        self.template_path = Config.TEMPLATE_PDF_PATH

        # Load Montserrat fonts (Gotham substitute)
        self.font_bold = pymupdf.Font(fontfile=Config.FONT_BOLD)
        self.font_bold_italic = pymupdf.Font(fontfile=Config.FONT_BOLD_ITALIC)
        self.font_light = pymupdf.Font(fontfile=Config.FONT_LIGHT)

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

        Design spec:
        - Name:     Gotham Bold Italic, 12.97pt, #F4F0F9
        - Position: Gotham Bold, 12.97pt, #F4F0F9
        - Date:     Gotham Bold, 12.97pt, #F4F0F9
        """
        name = user.get("name", "")
        position = user.get("position", "")
        display_date = user.get("date") or date.today().isoformat()

        # Name — Montserrat Bold Italic, 12.97pt, #F4F0F9
        self._insert_font_text(page, 160, 226, name,
                               font=self.font_bold_italic,
                               fontsize=12.97, color=_LIGHT)

        # Position — Montserrat Bold, 12.97pt, #F4F0F9
        self._insert_font_text(page, 374, 226, position,
                               font=self.font_bold,
                               fontsize=12.97, color=_LIGHT)

        # Date — Montserrat Bold, 12.97pt, #F4F0F9
        self._insert_font_text(page, 177, 243, display_date,
                               font=self.font_bold,
                               fontsize=12.97, color=_LIGHT)

    # ── Results ──────────────────────────────────────────────────────

    def _fill_results(self, page, results: dict):
        """Fill overall level and score.

        Scoring system:
        - 4 dimensions x 2 questions x scale 1-5 = max 10 per dim, max 40 total
        - n8n sends overall_score as percentage (0-100)
        - PDF must display raw score: e.g. "23/ 40"

        Design spec:
        - Level:  Gotham Bold, 13.98pt, #65A6FA
        - Score:  Gotham Bold, 13.98pt, #F4F0F9
        """
        level = results.get("overall_level", "")
        score_pct = results.get("overall_score", 0)  # percentage 0-100

        # Convert percentage to raw score (scale: max 40 points)
        num_dims = len(results.get("dimensions", []))
        max_per_dim = 10   # each dimension: 2 questions x scale 1-5
        max_score = num_dims * max_per_dim if num_dims > 0 else 40
        raw_score = round(score_pct * max_score / 100.0)

        # Level — Montserrat Bold, 13.98pt, #65A6FA
        self._insert_font_text(page, 221, 279, level.upper(),
                               font=self.font_bold,
                               fontsize=13.98, color=_CYAN)

        # Score — Montserrat Bold, 13.98pt, #F4F0F9
        score_text = f"{raw_score}/ {max_score}"
        self._insert_font_text(page, 194, 301, score_text,
                               font=self.font_bold,
                               fontsize=13.98, color=_LIGHT)

    # ── Summary ──────────────────────────────────────────────────────

    def _fill_summary(self, page, summary: str):
        """Fill the summary paragraph below the score.

        Design spec:
        - Gotham Light, 12pt, #FFFFFF, line spacing 16.51pt, align left
        """
        if not summary:
            return

        clean = self._strip_html(summary)

        # Summary area rect
        rect = pymupdf.Rect(27, 312, 559, 430)
        self._insert_paragraph(page, rect, clean,
                               font=self.font_light,
                               fontsize=12.0, color=_WHITE,
                               leading=16.51)

    # ── Chart bars ───────────────────────────────────────────────────

    def _fill_chart_bars(self, page, results: dict):
        """Draw horizontal bars for each dimension score.

        Scoring: each dimension has max 10 raw points (2 questions x scale 1-5).
        n8n sends scores as percentages (0-100).  We convert back to raw (0-10).

        Template chart axis goes 0-35 but real scale is 0-10, so we map
        raw_score onto the axis proportionally:
            pixel_x = chart_x0 + (raw_score / 10) * axis_length

        Template chart area (PyMuPDF coords, Y from top):
        - Grid line at score 0:  x = 214.8
        - Grid line at score 35: x = 512.4
        - Bar rows (4 bars):
            Row 0: y = 441.2 to 471.8  (I. Liderazgo e Influencia Social)
            Row 1: y = 475.2 to 505.8  (II. Empatia y Escucha Activa)
            Row 2: y = 509.2 to 539.9  (III. Delegacion y Desarrollo del Talento)
            Row 3: y = 543.3 to 573.9  (IV. Resiliencia y Adaptabilidad)
        """
        dimensions = results.get("dimensions", [])
        dim_levels = results.get("dimension_levels", [])

        chart_x0 = 214.8   # x at score=0 (grid line)
        chart_x35 = 512.4  # x at score=35 (grid line)
        axis_length = chart_x35 - chart_x0  # total pixel width of axis
        max_raw = 10        # max raw score per dimension
        corner_r = 2.5      # rounded corner radius (matches template)

        # Y positions for each bar row (PyMuPDF coords, Y from top of page)
        bar_rows = [
            (441.2, 471.8),  # Row 0 — I. Liderazgo e Influencia Social
            (475.2, 505.8),  # Row 1 — II. Empatia y Escucha Activa
            (509.2, 539.9),  # Row 2 — III. Delegacion y Desarrollo del Talento
            (543.3, 573.9),  # Row 3 — IV. Resiliencia y Adaptabilidad
        ]

        for i, dim in enumerate(dimensions):
            if i >= len(bar_rows):
                break

            score_pct = dim.get("score", 0) if isinstance(dim, dict) else dim.score
            # Convert percentage (0-100) to raw score (0-10)
            raw_score = score_pct * max_raw / 100.0

            level = "Intermedio"
            if i < len(dim_levels):
                lv = dim_levels[i]
                level = lv.get("level", "Intermedio") if isinstance(lv, dict) else lv.level

            # Bar color based on level
            bar_color = _BAR_COLORS.get(level, _BAR_COLORS["Intermedio"])

            y_top, y_bottom = bar_rows[i]

            # Erase the existing template bar (covers full area including corners)
            erase_rect = pymupdf.Rect(
                chart_x0 - corner_r - 1, y_top,
                chart_x35 + corner_r + 1, y_bottom,
            )
            page.draw_rect(erase_rect, color=None, fill=_BG_RGB)

            # Draw new bar with rounded corners
            if raw_score > 0:
                # Map raw score (0-10) to axis pixels (0 to axis_length)
                bar_px = (raw_score / max_raw) * axis_length
                bar_x_end = chart_x0 + bar_px
                # Clamp to chart boundary
                bar_x_end = min(bar_x_end, chart_x35)

                bar_rect = pymupdf.Rect(
                    chart_x0 - corner_r, y_top,
                    bar_x_end + corner_r, y_bottom,
                )
                page.draw_rect(
                    bar_rect, color=None, fill=bar_color,
                    radius=corner_r / (y_bottom - y_top),
                )

    # ── Learning path ────────────────────────────────────────────────

    def _fill_learning_path(self, page, learning_path: str):
        """Fill the learning path text below its title.

        Design spec:
        - Main text: Gotham Light, 12.5pt, #FFFFFF, line spacing 17.26pt, align left
        - Bold emphasis: Gotham Bold, 12.5pt, #FFFFFF (for <b>...</b> or **...** tags)
        """
        if not learning_path:
            return

        # Title "Ruta de Aprendizaje Recomendada" ends at y=616.9
        # Add ~10pt gap (same as summary section) → start at y=627
        rect = pymupdf.Rect(27, 627, 559, 820)
        self._insert_rich_paragraph(page, rect, learning_path,
                                    fontsize=12.5, color=_WHITE,
                                    leading=17.26)

    # ── Helper methods ───────────────────────────────────────────────

    def _insert_font_text(self, page, x: float, y: float, text: str,
                          font=None, fontsize: float = 11, color=_WHITE):
        """Insert a single line of text using a custom Font object."""
        if not text:
            return

        writer = pymupdf.TextWriter(page.rect)
        writer.append(pymupdf.Point(x, y), text, font=font, fontsize=fontsize)
        writer.write_text(page, color=color)

    def _insert_paragraph(self, page, rect: pymupdf.Rect, text: str,
                          font=None, fontsize: float = 10, color=_WHITE,
                          leading: float = None):
        """Insert word-wrapped plain text inside a rectangle using TextWriter.

        Uses manual line-breaking for proper leading (line spacing) control.
        """
        if not text:
            return

        if font is None:
            font = self.font_light
        if leading is None:
            leading = fontsize * 1.4

        words = text.split()
        if not words:
            return

        x0, y0, x1, _ = rect
        max_width = x1 - x0
        current_y = y0 + fontsize  # baseline of first line

        writer = pymupdf.TextWriter(page.rect)
        line = ""

        for word in words:
            test_line = f"{line} {word}".strip() if line else word
            text_width = font.text_length(test_line, fontsize=fontsize)

            if text_width <= max_width:
                line = test_line
            else:
                # Write current line
                if line:
                    writer.append(pymupdf.Point(x0, current_y), line,
                                  font=font, fontsize=fontsize)
                    current_y += leading
                line = word

            if current_y > rect.y1:
                break

        # Write last line
        if line and current_y <= rect.y1:
            writer.append(pymupdf.Point(x0, current_y), line,
                          font=font, fontsize=fontsize)

        writer.write_text(page, color=color)

    def _insert_rich_paragraph(self, page, rect: pymupdf.Rect, text: str,
                               fontsize: float = 12.5, color=_WHITE,
                               leading: float = None):
        """Insert word-wrapped text with bold spans inside a rectangle.

        Supports <b>...</b> and <strong>...</strong> HTML tags for bold emphasis.
        Everything else renders in Light font.
        """
        if not text:
            return

        if leading is None:
            leading = fontsize * 1.4

        # Parse text into segments: [(text, is_bold), ...]
        segments = self._parse_bold_segments(text)

        x0, y0, x1, _ = rect
        max_width = x1 - x0
        current_y = y0 + fontsize  # baseline of first line
        current_x = x0

        writer = pymupdf.TextWriter(page.rect)

        for segment_text, is_bold in segments:
            font = self.font_bold if is_bold else self.font_light
            words = segment_text.split()

            for word in words:
                # Measure word width
                word_text = word + " "
                word_width = font.text_length(word_text, fontsize=fontsize)

                # Check if word fits on current line
                if current_x + word_width > x1 and current_x > x0:
                    # New line
                    current_y += leading
                    current_x = x0

                if current_y > rect.y1:
                    break

                # Write word
                writer.append(pymupdf.Point(current_x, current_y), word_text,
                              font=font, fontsize=fontsize)
                current_x += word_width

            if current_y > rect.y1:
                break

        writer.write_text(page, color=color)

    @staticmethod
    def _parse_bold_segments(text: str) -> list:
        """Parse text into segments of (text, is_bold).

        Supports:
        - <b>...</b> and <strong>...</strong> HTML tags
        - **...** markdown bold

        Returns list of (text_content, is_bold) tuples.
        """
        # First normalize: replace <br/> with spaces
        text = re.sub(r'<br\s*/?>', ' ', text)

        # Convert **text** to <b>text</b> for uniform processing
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

        segments = []
        # Split by <b>...</b> and <strong>...</strong>
        pattern = r'(<b>.*?</b>|<strong>.*?</strong>)'
        parts = re.split(pattern, text, flags=re.DOTALL)

        for part in parts:
            if not part:
                continue
            if part.startswith('<b>') and part.endswith('</b>'):
                inner = part[3:-4].strip()
                if inner:
                    segments.append((inner, True))
            elif part.startswith('<strong>') and part.endswith('</strong>'):
                inner = part[8:-9].strip()
                if inner:
                    segments.append((inner, True))
            else:
                # Remove any remaining HTML tags
                clean = re.sub(r'<[^>]+>', '', part).strip()
                if clean:
                    segments.append((clean, False))

        # If no segments found (no tags at all), return whole text as plain
        if not segments:
            clean = re.sub(r'<[^>]+>', '', text).strip()
            if clean:
                segments.append((clean, False))

        return segments

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text, keeping plain content."""
        # Replace <br/> and <br> with newlines
        text = re.sub(r'<br\s*/?>', '\n', text)
        # Remove all other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
