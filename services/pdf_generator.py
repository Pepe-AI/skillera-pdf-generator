"""
PDF generation service module.
Generates branded leadership diagnostic PDF reports using ReportLab.
Layout matches the reference design: gradient background, large logo
top-left, large centered title, left-aligned user data, cyan section
titles, chart with legend on top, and rich text support.
"""

from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from config import Config
from services.chart_generator import ChartGenerator


class PDFGenerator:
    """Service class for generating branded PDF leadership reports."""

    def __init__(self):
        """Initialize the PDF generator with brand settings."""
        self.chart_gen = ChartGenerator()
        self.page_w, self.page_h = A4  # 595.28, 841.89
        self.margin = Config.PDF_MARGIN_LEFT
        self.content_w = Config.PDF_CONTENT_WIDTH

        # Precompute ReportLab color objects
        self.bg_color = HexColor(Config.COLOR_BACKGROUND)
        self.primary_color = HexColor(Config.COLOR_PRIMARY)
        self.secondary_color = HexColor(Config.COLOR_SECONDARY)
        self.text_color = HexColor(Config.COLOR_TEXT_LIGHT)
        self.muted_color = HexColor("#A0AEC0")
        self.cyan_color = HexColor(Config.COLOR_CYAN)

        # Level-to-color mapping
        self.level_colors = {
            "Avanzado": HexColor(Config.CHART_COLORS["avanzado"]),
            "Intermedio": HexColor(Config.CHART_COLORS["intermedio"]),
            "Principiante": HexColor(Config.CHART_COLORS["principiante"]),
        }

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Generate the full leadership diagnostic PDF.

        Args:
            data: Validated PDFRequest dict with keys: user, results, ai_content

        Returns:
            BytesIO containing the complete PDF document.
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Track vertical position (Y from bottom, starts at top)
        y = self.page_h

        # === BACKGROUND (gradient) ===
        self._draw_gradient_background(c)

        # === SECTION 1: LOGO + SLOGAN ===
        y = self._draw_header(c, y)

        # === SECTION 2: TITLE ===
        y = self._draw_title(c, y)

        # === SECTION 3: USER DATA ===
        y = self._draw_user_data(c, y, data["user"])

        # === SECTION 4: GENERAL RESULT ===
        y = self._draw_general_result(c, y, data["results"])

        # === SECTION 5: SUMMARY (no section title, direct paragraph) ===
        y = self._draw_summary(c, y, data["ai_content"]["summary"])

        # === SECTION 6: CHART with title ===
        y = self._draw_chart_section(c, y, data["results"])

        # === SECTION 7: LEARNING PATH ===
        y = self._draw_learning_path(c, y, data["ai_content"]["learning_path"])

        c.save()
        buffer.seek(0)
        return buffer

    # ── Background ────────────────────────────────────────────────────

    def _draw_gradient_background(self, c: canvas.Canvas):
        """Draw a purple gradient background matching the reference PDF."""
        strips = 120
        strip_h = self.page_h / strips

        for i in range(strips):
            t = i / strips  # 0 = top, 1 = bottom
            r = Config.GRADIENT_TOP_R + t * (Config.GRADIENT_BOT_R - Config.GRADIENT_TOP_R)
            g = Config.GRADIENT_TOP_G + t * (Config.GRADIENT_BOT_G - Config.GRADIENT_TOP_G)
            b = Config.GRADIENT_TOP_B + t * (Config.GRADIENT_BOT_B - Config.GRADIENT_TOP_B)
            c.setFillColorRGB(r, g, b)
            y = self.page_h - (i * strip_h)
            c.rect(0, y - strip_h, self.page_w, strip_h + 0.5, fill=1, stroke=0)

        # (No top accent bar — clean gradient only)

    # ── Header: Logo + Slogan ─────────────────────────────────────────

    def _get_logo(self) -> ImageReader:
        """Load the full Skillera logo (white text + lavender icons on
        transparent background).  Ready to use on dark backgrounds.
        """
        return ImageReader(Config.LOGO_FULL_PATH)

    def _draw_header_banner(self, c: canvas.Canvas):
        """Draw the curved purple banner shape in the top-left corner.

        The reference PDF shows a rounded purple blob that:
        - Covers the top-left area of the page
        - Has a rounded right edge (top-right corner is rounded)
        - Curves smoothly down to a rounded bottom
        - Contains the Skillera logo and slogan
        """
        banner_color = HexColor(Config.COLOR_BANNER)
        c.setFillColor(banner_color)
        c.setStrokeColor(banner_color)

        # Key coordinates (ReportLab: Y=0 at bottom, Y=page_h at top)
        top = self.page_h                   # 841.89
        banner_h = 140                       # ~17% of page height
        bottom = top - banner_h              # ~702

        # Right edge position at the top of the banner
        right_top = self.page_w * 0.57       # ~339 pt

        # Radius for the top-right rounded corner
        corner_r = 30

        p = c.beginPath()
        # Start at top-left corner (edge of page)
        p.moveTo(0, top)
        # Straight line across top, stopping before rounded corner
        p.lineTo(right_top - corner_r, top)
        # Rounded top-right corner (quarter circle arc via bezier)
        kappa = 0.5522847498  # bezier constant for circular arcs
        p.curveTo(
            right_top - corner_r + corner_r * kappa, top,    # cp1
            right_top, top - corner_r + corner_r * kappa,    # cp2
            right_top, top - corner_r,                       # end
        )
        # Right edge curves down and left toward the bottom
        # The reference shape stays fairly vertical on the right, then
        # curves sharply left near the bottom — no long tail.
        p.curveTo(
            right_top, top - banner_h * 0.60,     # cp1: straight down
            right_top - 20, top - banner_h * 0.75, # cp2: start curving left
            right_top * 0.42, bottom + 10,         # end: bottom area
        )
        # Bottom curve sweeps left back to the page edge
        p.curveTo(
            right_top * 0.18, bottom - 10,     # cp1
            0, bottom + 8,                     # cp2
            0, bottom + 8,                     # end: left edge
        )
        # Close path back up to start
        p.lineTo(0, top)
        p.close()

        c.drawPath(p, fill=1, stroke=0)

    def _draw_header(self, c: canvas.Canvas, y: float) -> float:
        """Draw the purple banner with logo and slogan inside it."""
        # 1) Draw the curved banner shape
        self._draw_header_banner(c)

        # 2) Place logo inside the banner — bigger, closer to top-left
        y -= 18  # small top padding

        # Logo dimensions — original is ~3:1 ratio (2048x682)
        logo_h = 60
        logo_w = logo_h * 3  # ~180 pts wide
        logo_x = self.margin - 5  # slightly closer to edge
        y -= logo_h

        try:
            logo = self._get_logo()
            c.drawImage(
                logo, logo_x, y,
                width=logo_w, height=logo_h,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            # Fallback: just draw text
            c.setFillColor(self.text_color)
            c.setFont(Config.PDF_FONT_BOLD, 36)
            c.drawString(logo_x, y + 10, "Skillera")

        # 3) Slogan just below logo
        y -= 6
        c.setFillColor(HexColor("#C4B5D9"))  # light lavender on banner
        c.setFont(Config.PDF_FONT, 9)
        c.drawString(self.margin, y, "Talento en transformaci\u00f3n para el futuro")

        # Space after banner before title
        y -= 45
        return y

    # ── Title ─────────────────────────────────────────────────────────

    def _draw_title(self, c: canvas.Canvas, y: float) -> float:
        """Draw large centered report title."""
        c.setFillColor(self.text_color)
        c.setFont(Config.PDF_FONT_BOLD, Config.PDF_FONT_SIZE_TITLE)

        # Two lines centered
        c.drawCentredString(self.page_w / 2, y, "DIAGN\u00d3STICO PERSONALIZADO DE")
        y -= 34
        c.drawCentredString(self.page_w / 2, y, "LIDERAZGO 2030")

        y -= 30
        return y

    # ── User Data ─────────────────────────────────────────────────────

    def _draw_user_data(self, c: canvas.Canvas, y: float, user: dict) -> float:
        """Draw user info: name, position, date — left-aligned, matching reference."""
        display_date = user.get("date") or date.today().isoformat()

        # Line 1: "Elaborado para: Name Puesto/Rol: Position"
        style_user = ParagraphStyle(
            "user_data",
            fontName=Config.PDF_FONT,
            fontSize=11,
            textColor=self.text_color,
            leading=16,
        )
        line1 = (
            f'<b>Elaborado para:</b> <i>{user["name"]}</i> '
            f'<b>Puesto/Rol: {user["position"]}</b>'
        )
        para1 = Paragraph(line1, style_user)
        pw1, ph1 = para1.wrap(self.content_w, 50)
        para1.drawOn(c, self.margin, y - ph1)
        y -= (ph1 + 4)

        # Line 2: "Fecha de Emisión: date"
        line2 = f'<b>Fecha de Emisi\u00f3n: {display_date}</b>'
        para2 = Paragraph(line2, style_user)
        pw2, ph2 = para2.wrap(self.content_w, 30)
        para2.drawOn(c, self.margin, y - ph2)
        y -= (ph2 + 20)

        return y

    # ── General Result ────────────────────────────────────────────────

    def _draw_general_result(self, c: canvas.Canvas, y: float, results: dict) -> float:
        """Draw overall level and score — matching reference layout."""
        level = results["overall_level"]
        score = results["overall_score"]

        # Calculate max score based on number of dimensions
        num_dims = len(results.get("dimensions", []))
        max_per_dim = 35
        max_score = num_dims * max_per_dim if num_dims > 0 else 140

        # Line 1: "Tu Resultado General: INTERMEDIO" in cyan
        style_result = ParagraphStyle(
            "result_title",
            fontName=Config.PDF_FONT,
            fontSize=13,
            textColor=HexColor(Config.COLOR_CYAN),
            leading=18,
        )
        line1 = f'Tu Resultado General: <b>{level.upper()}</b>'
        para1 = Paragraph(line1, style_result)
        pw1, ph1 = para1.wrap(self.content_w, 30)
        para1.drawOn(c, self.margin, y - ph1)
        y -= (ph1 + 4)

        # Line 2: "Puntuación Global: score/ max" in white bold
        style_score = ParagraphStyle(
            "result_score",
            fontName=Config.PDF_FONT_BOLD,
            fontSize=13,
            textColor=self.text_color,
            leading=18,
        )
        score_display = f"{score:.0f}"
        line2 = f'<b>Puntuaci\u00f3n Global: {score_display}/ {max_score}</b>'
        para2 = Paragraph(line2, style_score)
        pw2, ph2 = para2.wrap(self.content_w, 30)
        para2.drawOn(c, self.margin, y - ph2)
        y -= (ph2 + 12)

        return y

    # ── Summary (no section title) ───────────────────────────────────

    def _draw_summary(self, c: canvas.Canvas, y: float, summary: str) -> float:
        """Draw the AI summary as a direct paragraph (no section header)."""
        style = ParagraphStyle(
            "summary_text",
            fontName=Config.PDF_FONT,
            fontSize=Config.PDF_FONT_SIZE_BODY,
            textColor=self.text_color,
            leading=14,
            alignment=TA_JUSTIFY,
        )
        para = Paragraph(summary.replace("\n", "<br/>"), style)
        para_w, para_h = para.wrap(self.content_w, 400)

        # Check page space
        if y - para_h < Config.PDF_MARGIN_BOTTOM + 40:
            c.showPage()
            self._draw_gradient_background(c)
            y = self.page_h - self.margin

        para.drawOn(c, self.margin, y - para_h)
        y -= (para_h + 18)

        return y

    # ── Chart Section ─────────────────────────────────────────────────

    def _draw_chart_section(self, c: canvas.Canvas, y: float, results: dict) -> float:
        """Draw section title + competency chart."""
        # Section title in cyan
        title_text = "Perfil de Competencias: Tu Puntuaci\u00f3n por Dimensi\u00f3n"
        style_title = ParagraphStyle(
            "chart_title",
            fontName=Config.PDF_FONT_BOLD,
            fontSize=13,
            textColor=HexColor(Config.COLOR_CYAN),
            leading=16,
        )
        para_title = Paragraph(title_text, style_title)
        ptw, pth = para_title.wrap(self.content_w, 30)
        para_title.drawOn(c, self.margin, y - pth)
        y -= (pth + 8)

        # Generate chart image
        dimensions = [
            d if isinstance(d, dict) else d.dict()
            for d in results["dimensions"]
        ]
        dim_levels = [
            d if isinstance(d, dict) else d.dict()
            for d in results["dimension_levels"]
        ]
        chart_buffer = self.chart_gen.generate_chart(dimensions, dim_levels)

        # Embed in PDF
        chart_img = ImageReader(chart_buffer)
        chart_w = self.content_w
        chart_h = 190

        # Check page space
        if y - chart_h < Config.PDF_MARGIN_BOTTOM + 40:
            c.showPage()
            self._draw_gradient_background(c)
            y = self.page_h - self.margin

        chart_y = y - chart_h
        c.drawImage(
            chart_img, self.margin, chart_y,
            width=chart_w, height=chart_h,
            preserveAspectRatio=True, mask="auto",
        )

        y = chart_y - 12
        return y

    # ── Learning Path ─────────────────────────────────────────────────

    def _draw_learning_path(self, c: canvas.Canvas, y: float, learning_path: str) -> float:
        """Draw the learning path section with cyan title and rich text body."""
        # Section title in cyan italic-bold
        title_text = "Ruta de Aprendizaje Recomendada"
        style_title = ParagraphStyle(
            "lp_title",
            fontName=Config.PDF_FONT_BOLD_ITALIC,
            fontSize=13,
            textColor=HexColor(Config.COLOR_CYAN),
            leading=16,
        )
        para_title = Paragraph(title_text, style_title)
        ptw, pth = para_title.wrap(self.content_w, 30)

        # Check page space for title + some body text
        if y - pth - 60 < Config.PDF_MARGIN_BOTTOM:
            c.showPage()
            self._draw_gradient_background(c)
            y = self.page_h - self.margin

        para_title.drawOn(c, self.margin, y - pth)
        y -= (pth + 8)

        # Body text — supports <b> tags for bold words
        style_body = ParagraphStyle(
            "lp_body",
            fontName=Config.PDF_FONT,
            fontSize=Config.PDF_FONT_SIZE_BODY,
            textColor=self.text_color,
            leading=14,
            alignment=TA_JUSTIFY,
        )
        body_text = learning_path.replace("\n", "<br/>")
        para_body = Paragraph(body_text, style_body)
        pbw, pbh = para_body.wrap(self.content_w, 500)

        # Check page space
        if y - pbh < Config.PDF_MARGIN_BOTTOM:
            c.showPage()
            self._draw_gradient_background(c)
            y = self.page_h - self.margin

        para_body.drawOn(c, self.margin, y - pbh)
        y -= (pbh + 15)

        return y
