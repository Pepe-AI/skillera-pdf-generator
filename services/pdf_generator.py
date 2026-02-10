"""
PDF generation service module.
Generates branded leadership diagnostic PDF reports using ReportLab.
"""

from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

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

        # Level-to-color mapping for result badge
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

        # === BACKGROUND ===
        self._draw_background(c)

        # === SECTION 1: LOGO + SLOGAN ===
        y = self._draw_header(c, y)

        # === SECTION 2: TITLE ===
        y = self._draw_title(c, y)

        # === SECTION 3: USER DATA ===
        y = self._draw_user_data(c, y, data["user"])

        # === SECTION 4: GENERAL RESULT ===
        y = self._draw_general_result(c, y, data["results"])

        # === SECTION 5: SUMMARY ===
        y = self._draw_text_section(c, y, "RESUMEN EJECUTIVO", data["ai_content"]["summary"])

        # === SECTION 6: CHART ===
        y = self._draw_chart(c, y, data["results"])

        # === SECTION 7: LEARNING PATH ===
        y = self._draw_text_section(c, y, "RUTA DE APRENDIZAJE", data["ai_content"]["learning_path"])

        # === SECTION 8: FOOTER ===
        self._draw_footer(c)

        c.save()
        buffer.seek(0)
        return buffer

    def _draw_background(self, c: canvas.Canvas):
        """Fill the entire page with the dark background color."""
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

    def _draw_header(self, c: canvas.Canvas, y: float) -> float:
        """Draw logo and slogan at top of page."""
        y -= self.margin  # Top margin

        # Logo: centered, 60x60pt
        logo_h = 60
        logo_w = 60
        logo_x = (self.page_w - logo_w) / 2
        y -= logo_h

        try:
            logo = ImageReader(Config.LOGO_PATH)
            c.drawImage(
                logo, logo_x, y,
                width=logo_w, height=logo_h,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass  # Skip logo if not found

        # Slogan below logo
        y -= 18
        c.setFillColor(self.secondary_color)
        c.setFont(Config.PDF_FONT, 10)
        c.drawCentredString(self.page_w / 2, y, Config.SLOGAN)

        y -= 15
        return y

    def _draw_title(self, c: canvas.Canvas, y: float) -> float:
        """Draw main report title."""
        y -= 10
        c.setFillColor(self.text_color)
        c.setFont(Config.PDF_FONT_BOLD, Config.PDF_FONT_SIZE_TITLE)
        c.drawCentredString(self.page_w / 2, y, "DIAGNOSTICO PERSONALIZADO")
        y -= 22
        c.drawCentredString(self.page_w / 2, y, "DE LIDERAZGO 2030")

        # Decorative line
        y -= 12
        c.setStrokeColor(self.primary_color)
        c.setLineWidth(2)
        line_half = 100
        c.line(self.page_w / 2 - line_half, y, self.page_w / 2 + line_half, y)

        y -= 15
        return y

    def _draw_user_data(self, c: canvas.Canvas, y: float, user: dict) -> float:
        """Draw name, position, and date."""
        c.setFillColor(self.text_color)
        c.setFont(Config.PDF_FONT_BOLD, 12)
        c.drawCentredString(self.page_w / 2, y, user["name"].upper())

        y -= 16
        c.setFont(Config.PDF_FONT, 10)
        c.setFillColor(self.secondary_color)
        c.drawCentredString(self.page_w / 2, y, user["position"])

        y -= 14
        display_date = user.get("date") or date.today().isoformat()
        c.setFont(Config.PDF_FONT, 9)
        c.setFillColor(self.muted_color)
        c.drawCentredString(self.page_w / 2, y, f"Fecha: {display_date}")

        y -= 20
        return y

    def _draw_general_result(self, c: canvas.Canvas, y: float, results: dict) -> float:
        """Draw overall level badge and score."""
        level = results["overall_level"]
        score = results["overall_score"]
        level_color = self.level_colors.get(level, self.secondary_color)

        # Label
        c.setFillColor(self.text_color)
        c.setFont(Config.PDF_FONT_BOLD, 11)
        c.drawCentredString(self.page_w / 2, y, "RESULTADO GENERAL")
        y -= 25

        # Rounded rectangle badge
        badge_w = 180
        badge_h = 32
        badge_x = (self.page_w - badge_w) / 2
        badge_y = y - badge_h + 5

        c.setFillColor(level_color)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, radius=8, fill=1, stroke=0)

        # Level text inside badge
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont(Config.PDF_FONT_BOLD, 14)
        c.drawCentredString(self.page_w / 2, badge_y + 10, level.upper())

        y = badge_y - 8

        # Score below badge
        c.setFillColor(self.text_color)
        c.setFont(Config.PDF_FONT_BOLD, 20)
        c.drawCentredString(self.page_w / 2, y, f"{score:.0f}%")

        y -= 8
        c.setFont(Config.PDF_FONT, 9)
        c.setFillColor(self.muted_color)
        c.drawCentredString(self.page_w / 2, y, "Puntuacion general")

        y -= 25
        return y

    def _draw_text_section(self, c: canvas.Canvas, y: float, title: str, body: str) -> float:
        """Draw a titled text section with word-wrapped body."""
        # Section title
        c.setFillColor(self.primary_color)
        c.setFont(Config.PDF_FONT_BOLD, 12)
        c.drawString(self.margin, y, title)
        y -= 5

        # Underline
        c.setStrokeColor(self.primary_color)
        c.setLineWidth(1)
        title_width = c.stringWidth(title, Config.PDF_FONT_BOLD, 12)
        c.line(self.margin, y, self.margin + title_width, y)
        y -= 14

        # Body text with word wrap using Paragraph
        style = ParagraphStyle(
            "body_text",
            fontName=Config.PDF_FONT,
            fontSize=Config.PDF_FONT_SIZE_BODY,
            textColor=self.text_color,
            leading=14,
            alignment=TA_JUSTIFY,
        )
        para = Paragraph(body.replace("\n", "<br/>"), style)
        para_w, para_h = para.wrap(self.content_w, 500)

        # Check if we need a new page
        if y - para_h < Config.PDF_MARGIN_BOTTOM + 40:
            c.showPage()
            self._draw_background(c)
            y = self.page_h - self.margin

        para.drawOn(c, self.margin, y - para_h)
        y -= (para_h + 15)

        return y

    def _draw_chart(self, c: canvas.Canvas, y: float, results: dict) -> float:
        """Generate and embed the competency chart."""
        # Section title
        title_text = "COMPETENCIAS POR DIMENSION"
        c.setFillColor(self.primary_color)
        c.setFont(Config.PDF_FONT_BOLD, 12)
        c.drawString(self.margin, y, title_text)
        y -= 5
        c.setStrokeColor(self.primary_color)
        c.setLineWidth(1)
        title_width = c.stringWidth(title_text, Config.PDF_FONT_BOLD, 12)
        c.line(self.margin, y, self.margin + title_width, y)
        y -= 10

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
        chart_h = 180

        # Check page space
        if y - chart_h < Config.PDF_MARGIN_BOTTOM + 40:
            c.showPage()
            self._draw_background(c)
            y = self.page_h - self.margin

        chart_y = y - chart_h
        c.drawImage(
            chart_img, self.margin, chart_y,
            width=chart_w, height=chart_h,
            preserveAspectRatio=True, mask="auto",
        )

        y = chart_y - 15
        return y

    def _draw_footer(self, c: canvas.Canvas):
        """Draw footer at bottom of current page."""
        footer_y = 25
        c.setFillColor(self.muted_color)
        c.setFont(Config.PDF_FONT, 7)
        c.drawCentredString(
            self.page_w / 2, footer_y,
            f"\u00a9 {date.today().year} Skillera. Todos los derechos reservados.",
        )
        c.drawCentredString(
            self.page_w / 2, footer_y - 10,
            "Este documento es confidencial y fue generado automaticamente.",
        )
