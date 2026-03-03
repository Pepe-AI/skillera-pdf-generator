"""
IE PDF Generator — Diagnostico de Inteligencia Emocional
Pure ReportLab generation (A4, multi-page). No template overlay, no pypdf.
"""

import os
import math
from io import BytesIO
from datetime import date
from xml.sax.saxutils import escape as _esc

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Page constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE_W, PAGE_H = A4          # 595.28 x 841.89
MARGIN    = 40
CONTENT_W = PAGE_W - 2 * MARGIN   # ~515
FOOTER_H  = 44

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Colors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BG       = HexColor("#1A0533")
HDR_HI   = HexColor("#3D1A6E")
WHITE    = HexColor("#FFFFFF")
LIGHT    = HexColor("#F4F0F9")
TEAL     = HexColor("#3CCBB2")
ACCENT   = HexColor("#6B46C1")
MUTED    = HexColor("#B8A9D4")
FOOTER_C = HexColor("#0F0420")
TRACK    = HexColor("#1F0D3D")
CARD_BG  = HexColor("#241052")

LVL_CLR = {
    "Bajo":  HexColor("#A0AEC0"),
    "Medio": HexColor("#667EEA"),
    "Alto":  HexColor("#9F7AEA"),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Asset paths
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_ASSETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets",
)
LOGO_PATH  = os.path.join(_ASSETS, "logo_transparent.png")
IMAGE_PATH = os.path.join(_ASSETS, "image_bloques.jpeg")
FONTS_DIR  = os.path.join(_ASSETS, "fonts")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Font registration (Montserrat → Helvetica fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_FONTS_OK = False


def _init_fonts():
    global _FONTS_OK
    if _FONTS_OK:
        return
    try:
        for alias, fname in [
            ("MontB",  "Montserrat-Bold.ttf"),
            ("MontL",  "Montserrat-Light.ttf"),
            ("MontBI", "Montserrat-BoldItalic.ttf"),
        ]:
            pdfmetrics.registerFont(TTFont(alias, os.path.join(FONTS_DIR, fname)))
        _FONTS_OK = True
    except Exception:
        pass


def _fn(style="r"):
    """Return font name.  b=bold  r=regular/light  i=bold-italic"""
    if _FONTS_OK:
        return {"b": "MontB", "r": "MontL", "i": "MontBI"}.get(style, "MontL")
    return {
        "b": "Helvetica-Bold",
        "r": "Helvetica",
        "i": "Helvetica-BoldOblique",
    }.get(style, "Helvetica")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Static text content per level
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IE_CONTENT = {
    "Bajo": {
        "frase": "Tus emociones suelen gestionarse de forma reactiva o evitativa.",
        "descripcion": {
            "parrafo1": (
                "Hay poca conciencia emocional y alto impacto en decisiones y relaciones. "
                "Tiendes a reaccionar de forma autom\u00e1tica frente a tus emociones, especialmente "
                "bajo presi\u00f3n o conflicto. Puede haber dificultad para identificar con claridad "
                "lo que sientes o para regularlo antes de actuar."
            ),
            "bullets_header": "Es posible que:",
            "bullets": [
                "Reacciones impulsivamente o evites conversaciones inc\u00f3modas.",
                "Te cueste separar el hecho de la emoci\u00f3n.",
                "Las emociones influyan en tus decisiones sin que lo notes plenamente.",
                "Haya impacto frecuente en relaciones laborales o personales.",
            ],
            "parrafo2": (
                "Este nivel no habla de incapacidad, sino de bajo entrenamiento emocional "
                "consciente. Muchas personas operan desde este punto sin haber desarrollado "
                "herramientas formales de regulaci\u00f3n."
            ),
        },
        "recs": [
            {
                "titulo": "Entrena la identificaci\u00f3n emocional diaria",
                "subtitulo": "Al final del d\u00eda preg\u00fantate:",
                "bullets": [
                    "\u00bfQu\u00e9 sent\u00ed hoy?",
                    "\u00bfEn qu\u00e9 momento fue m\u00e1s intenso?",
                    "\u00bfC\u00f3mo reaccion\u00e9?",
                ],
                "bold_final": "Nombrar la emoci\u00f3n reduce su intensidad.",
            },
            {
                "titulo": "Introduce la pausa de 90 segundos",
                "cuerpo": (
                    "Antes de responder en situaciones tensas, respira profundo y retrasa "
                    "tu reacci\u00f3n al menos 90 segundos. Esto activa la regulaci\u00f3n en lugar "
                    "del impulso."
                ),
            },
            {
                "titulo": "Separa hecho de interpretaci\u00f3n",
                "subtitulo": "Escribe una situaci\u00f3n reciente y div\u00eddela en:",
                "bullets": [
                    "Hecho objetivo",
                    "Lo que pens\u00e9",
                    "Lo que sent\u00ed",
                    "Lo que hice",
                ],
                "bold_final": "Esto desarrolla conciencia y rompe la reacci\u00f3n autom\u00e1tica.",
            },
        ],
    },
    "Medio": {
        "frase": (
            "Reconoces lo que sientes, pero bajo presi\u00f3n vuelves "
            "a patrones autom\u00e1ticos."
        ),
        "descripcion": {
            "parrafo1": (
                "Tienes una base s\u00f3lida para desarrollar mayor regulaci\u00f3n emocional. "
                "Hay conciencia, pero la regulaci\u00f3n todav\u00eda no es consistente."
            ),
            "bullets_header": "Es probable que:",
            "bullets": [
                "Escuches feedback, pero te afecte m\u00e1s de lo que reconoces.",
                "Identifiques emociones, pero no siempre sepas gestionarlas.",
                "Tengas buenas intenciones relacionales, aunque bajo estr\u00e9s se debiliten.",
            ],
            "parrafo2": (
                "Este nivel es una base s\u00f3lida. La diferencia entre nivel medio y alto "
                "suele estar en la consistencia, especialmente en momentos de tensi\u00f3n."
            ),
        },
        "recs": [
            {
                "titulo": "Practica la regulaci\u00f3n antes de conversar",
                "subtitulo": "Antes de una conversaci\u00f3n dif\u00edcil, preg\u00fantate:",
                "bullets": [
                    "\u00bfQu\u00e9 quiero lograr?",
                    "\u00bfDesde qu\u00e9 emoci\u00f3n estoy hablando?",
                ],
                "bold_final": "Esto aumenta la intenci\u00f3n consciente.",
            },
            {
                "titulo": "Pide feedback sobre tu impacto emocional",
                "subtitulo": "Pregunta a alguien de confianza:",
                "bullets": [
                    "\"Cuando estoy bajo presi\u00f3n, \u00bfc\u00f3mo me percibes?\"",
                ],
                "bold_final": (
                    "La autoconciencia se fortalece con retroalimentaci\u00f3n externa."
                ),
            },
            {
                "titulo": "Desarrolla vocabulario emocional m\u00e1s amplio",
                "cuerpo": (
                    "No es solo \"molesto\" o \"bien\", practica diferenciar: "
                    "frustrado, decepcionado, ansioso, inseguro, exigente, etc."
                ),
                "bold_final": "Mayor precisi\u00f3n = mejor regulaci\u00f3n.",
            },
        ],
    },
    "Alto": {
        "frase": "Gestionas tus emociones con conciencia y eliges c\u00f3mo responder.",
        "descripcion": {
            "parrafo1": "Probablemente:",
            "bullets_header": None,
            "bullets": [
                "Reconoces lo que sientes y c\u00f3mo influye en tus decisiones.",
                "Manejas conversaciones dif\u00edciles con equilibrio.",
                "Utilizas el feedback como herramienta de crecimiento.",
                "Influyes positivamente en el clima emocional de tu entorno.",
            ],
            "parrafo2": (
                "El reto en este nivel no es aprender lo b\u00e1sico, sino sostener "
                "la habilidad bajo alta carga emocional y liderazgo de otros."
            ),
        },
        "recs": [
            {
                "titulo": "Entrena la regulaci\u00f3n en situaciones de alta intensidad",
                "cuerpo": (
                    "Observa qu\u00e9 cambia cuando hay presi\u00f3n real "
                    "(tiempo, conflicto, jerarqu\u00eda)."
                ),
                "bold_final": "Ah\u00ed se mide el dominio.",
            },
            {
                "titulo": "Desarrolla inteligencia emocional interpersonal",
                "cuerpo": (
                    "No solo gestiones tus emociones; ayuda a otros a regularse."
                ),
                "bold_final": "Practica validar emociones antes de proponer soluciones.",
            },
            {
                "titulo": "Reflexiona sobre tus patrones invisibles",
                "subtitulo": (
                    "Incluso con alta inteligencia emocional, existen sesgos "
                    "o puntos ciegos. Preg\u00fantate:"
                ),
                "bullets": [
                    "\u00bfQu\u00e9 tipo de cr\u00edtica a\u00fan me incomoda?",
                    "\u00bfEn qu\u00e9 situaciones pierdo m\u00e1s neutralidad?",
                ],
            },
        ],
    },
}

# Static definition paragraphs
_IE_DEF = (
    "La inteligencia emocional es la capacidad de reconocer, comprender y "
    "gestionar las propias emociones, as\u00ed como las de los dem\u00e1s. Influye "
    "directamente en la toma de decisiones, las relaciones interpersonales "
    "y el liderazgo efectivo."
)
_IE_DEF2 = (
    "Este diagn\u00f3stico eval\u00faa tu nivel actual de gesti\u00f3n emocional a "
    "trav\u00e9s de 10 preguntas dise\u00f1adas para medir conciencia, regulaci\u00f3n "
    "y capacidad de respuesta emocional."
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Generator class
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class IEPDFGenerator:
    """Generates IE diagnostic PDFs using pure ReportLab (no template)."""

    def __init__(self):
        _init_fonts()

    # ── public entry point ────────────────────────────────────────────────

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Generate a complete IE diagnostic PDF.

        data = {
            "user":    {"name": str, "position": str},
            "results": {"total_score": float, "nivel": str}
        }
        Returns BytesIO with the PDF content.
        """
        nivel    = data["results"]["nivel"]
        score    = int(data["results"]["total_score"])
        name     = data["user"]["name"]
        position = data["user"]["position"]
        content  = IE_CONTENT[nivel]
        lcolor   = LVL_CLR.get(nivel, LVL_CLR["Medio"])

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setTitle(f"Diagnostico IE - {name}")

        # ── PAGE 1 ───────────────────────────────────────────────────
        self._bg(c)
        y = self._header(c, name, position)
        y = self._section_def(c, y)
        y = self._section_scale(c, y, nivel)
        y = self._section_results(c, y, score, nivel, lcolor, content["frase"])
        y = self._section_desc(c, y, content["descripcion"])
        self._footer(c, 1, 2)

        # ── PAGE 2 ───────────────────────────────────────────────────
        c.showPage()
        self._bg(c)
        y = PAGE_H - MARGIN
        y = self._section_recs(c, y, content["recs"])
        y = self._section_closing(c, y)
        self._footer(c, 2, 2)

        c.save()
        buf.seek(0)
        return buf

    # ══════════════════════════════════════════════════════════════════════
    # Shared drawing helpers
    # ══════════════════════════════════════════════════════════════════════

    def _bg(self, c):
        """Fill entire page with dark background."""
        c.setFillColor(BG)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def _footer(self, c, page, total):
        """Dark footer bar with Skillera branding."""
        c.setFillColor(FOOTER_C)
        c.rect(0, 0, PAGE_W, FOOTER_H, fill=1, stroke=0)
        c.setFont(_fn("r"), 7.5)
        c.setFillColor(MUTED)
        c.drawString(MARGIN, 18, "Skillera \u00b7 Talento en transformaci\u00f3n para el futuro")
        c.drawRightString(PAGE_W - MARGIN, 18, f"P\u00e1gina {page} de {total}")

    def _gradient_rect(self, c, x, y_bot, w, h, col_bot, col_top, steps=30):
        """Draw a vertical gradient (bottom color → top color)."""
        sh = h / steps
        for i in range(steps):
            t = i / max(steps - 1, 1)
            r = col_bot.red   + t * (col_top.red   - col_bot.red)
            g = col_bot.green + t * (col_top.green - col_bot.green)
            b = col_bot.blue  + t * (col_top.blue  - col_bot.blue)
            c.setFillColor(Color(r, g, b))
            c.rect(x, y_bot + i * sh, w, sh + 0.5, fill=1, stroke=0)

    def _para(self, c, text, x, y, width, font, size, color,
              align=TA_LEFT, leading=None):
        """Draw a wrapped paragraph. Returns y below the paragraph."""
        if not text:
            return y
        if leading is None:
            leading = round(size * 1.45)
        safe = _esc(str(text))
        style = ParagraphStyle(
            "p", fontName=font, fontSize=size,
            textColor=color, leading=leading, alignment=align,
        )
        p = Paragraph(safe, style)
        _, ph = p.wrap(width, 9999)
        p.drawOn(c, x, y - ph)
        return y - ph

    def _hex_badge(self, c, cx, cy, radius, fill_color, text, text_size=15):
        """Draw a pointy-top hexagonal badge with centered text."""
        path = c.beginPath()
        for i in range(6):
            angle = math.radians(60 * i + 90)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.close()
        c.setFillColor(fill_color)
        c.drawPath(path, fill=1, stroke=0)
        # Subtle lighter outline
        c.setStrokeColor(Color(
            min(fill_color.red + 0.15, 1.0),
            min(fill_color.green + 0.15, 1.0),
            min(fill_color.blue + 0.15, 1.0),
        ))
        c.setLineWidth(1.2)
        path2 = c.beginPath()
        for i in range(6):
            angle = math.radians(60 * i + 90)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            if i == 0:
                path2.moveTo(x, y)
            else:
                path2.lineTo(x, y)
        path2.close()
        c.drawPath(path2, fill=0, stroke=1)
        # Centered text
        c.setFont(_fn("b"), text_size)
        c.setFillColor(WHITE)
        c.drawCentredString(cx, cy - text_size * 0.35, text)

    def _safe_image(self, c, path, x, y, w, h, mask=None):
        """Draw an image if the file exists. Graceful no-op on failure."""
        if not os.path.isfile(path):
            return False
        try:
            kwargs = {"width": w, "height": h, "preserveAspectRatio": True}
            if mask:
                kwargs["mask"] = mask
            c.drawImage(path, x, y, **kwargs)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 1 — sections
    # ══════════════════════════════════════════════════════════════════════

    def _header(self, c, name, position):
        """Gradient header band with logo, title, and user info. Returns y."""
        hdr_h   = 160
        hdr_bot = PAGE_H - hdr_h   # ~682

        # Gradient background
        self._gradient_rect(c, 0, hdr_bot, PAGE_W, hdr_h, BG, HDR_HI)

        # Logo (top-left)
        self._safe_image(c, LOGO_PATH, MARGIN, PAGE_H - 50, 90, 26, mask="auto")

        # Date (top-right)
        c.setFont(_fn("r"), 7.5)
        c.setFillColor(MUTED)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 36,
                          date.today().strftime("%d/%m/%Y"))

        # Title — two lines
        c.setFont(_fn("b"), 17)
        c.setFillColor(WHITE)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 75, "DIAGN\u00d3STICO DE")
        c.setFont(_fn("b"), 22)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 100, "INTELIGENCIA EMOCIONAL")

        # Teal accent line
        c.setStrokeColor(TEAL)
        c.setLineWidth(2)
        ly = PAGE_H - 112
        c.line(PAGE_W / 2 - 55, ly, PAGE_W / 2 + 55, ly)

        # User info row
        info_y = PAGE_H - 135
        c.setFont(_fn("b"), 9.5)
        c.setFillColor(LIGHT)
        c.drawString(MARGIN + 5, info_y, "Nombre:")
        lbl_w = stringWidth("Nombre: ", _fn("b"), 9.5)
        c.setFont(_fn("r"), 9.5)
        # Autofit name
        disp_name = name
        fs_n = 9.5
        avail = 210
        while stringWidth(disp_name, _fn("r"), fs_n) > avail and fs_n > 7:
            fs_n -= 0.5
        c.setFont(_fn("r"), fs_n)
        c.drawString(MARGIN + 5 + lbl_w, info_y, disp_name)

        mid_x = PAGE_W / 2 + 10
        c.setFont(_fn("b"), 9.5)
        c.drawString(mid_x, info_y, "Puesto:")
        lbl_w2 = stringWidth("Puesto: ", _fn("b"), 9.5)
        c.setFont(_fn("r"), 9.5)
        # Autofit position
        disp_pos = position
        fs_p = 9.5
        avail_p = PAGE_W - MARGIN - mid_x - lbl_w2 - 5
        while stringWidth(disp_pos, _fn("r"), fs_p) > avail_p and fs_p > 7:
            fs_p -= 0.5
        c.setFont(_fn("r"), fs_p)
        c.drawString(mid_x + lbl_w2, info_y, disp_pos)

        return hdr_bot - 15

    def _section_def(self, c, y):
        """IE definition section. Returns y below."""
        # Title
        c.setFont(_fn("b"), 12)
        c.setFillColor(TEAL)
        c.drawString(MARGIN, y, "\u00bfQu\u00e9 es la Inteligencia Emocional?")
        y -= 16

        # Definition paragraph
        y = self._para(c, _IE_DEF, MARGIN, y, CONTENT_W,
                        _fn("r"), 9, LIGHT, align=TA_JUSTIFY)
        y -= 6

        # Second paragraph
        y = self._para(c, _IE_DEF2, MARGIN, y, CONTENT_W,
                        _fn("r"), 9, LIGHT, align=TA_JUSTIFY)
        y -= 16
        return y

    def _section_scale(self, c, y, nivel_actual):
        """Scoring scale with colored bars. Returns y below."""
        c.setFont(_fn("b"), 10.5)
        c.setFillColor(WHITE)
        c.drawString(MARGIN, y, "Escala de evaluaci\u00f3n:")
        y -= 20

        items = [
            ("Bajo",  "10 \u2013 20 puntos", LVL_CLR["Bajo"]),
            ("Medio", "21 \u2013 30 puntos", LVL_CLR["Medio"]),
            ("Alto",  "31 \u2013 40 puntos", LVL_CLR["Alto"]),
        ]
        for label, pts, clr in items:
            is_current = (label == nivel_actual)
            # Color chip
            c.setFillColor(clr)
            c.roundRect(MARGIN, y - 11, 45, 13, 3, fill=1, stroke=0)
            # Highlight border for current level
            if is_current:
                c.setStrokeColor(WHITE)
                c.setLineWidth(1.2)
                c.roundRect(MARGIN, y - 11, 45, 13, 3, fill=0, stroke=1)
            # Label
            c.setFont(_fn("b"), 9.5)
            c.setFillColor(WHITE if is_current else LIGHT)
            c.drawString(MARGIN + 52, y - 9, label)
            # Points
            c.setFont(_fn("r"), 8.5)
            c.setFillColor(MUTED)
            c.drawString(MARGIN + 100, y - 9, pts)
            y -= 19

        y -= 8
        return y

    def _section_results(self, c, y, score, nivel, lcolor, frase):
        """Score bar + hex badge + phrase. Returns y below."""
        # Section title
        c.setFont(_fn("b"), 13)
        c.setFillColor(WHITE)
        c.drawCentredString(PAGE_W / 2, y, "Tu Resultado")
        y -= 25

        # Progress bar
        bar_w = 320
        bar_h = 16
        bar_x = (PAGE_W - bar_w) / 2

        # Track
        c.setFillColor(TRACK)
        c.roundRect(bar_x, y - bar_h, bar_w, bar_h, 8, fill=1, stroke=0)
        # Fill
        fill_ratio = min(max(score / 40.0, 0), 1.0)
        fill_w = max(bar_w * fill_ratio, 16)
        c.setFillColor(lcolor)
        c.roundRect(bar_x, y - bar_h, fill_w, bar_h, 8, fill=1, stroke=0)
        # Score number inside bar
        c.setFont(_fn("b"), 10)
        c.setFillColor(WHITE)
        stxt = str(score)
        sw = stringWidth(stxt, _fn("b"), 10)
        sx = bar_x + fill_w - sw - 5
        if sx < bar_x + 3:
            sx = bar_x + 3
        c.drawString(sx, y - bar_h + 3.5, stxt)
        y -= bar_h + 8

        # Caption
        c.setFont(_fn("r"), 9.5)
        c.setFillColor(LIGHT)
        c.drawCentredString(PAGE_W / 2, y,
                            f"Tu puntuaci\u00f3n: {score} de 40 puntos")
        y -= 26

        # Hexagonal badge
        badge_r = 32
        cx = PAGE_W / 2
        cy = y - badge_r
        self._hex_badge(c, cx, cy, badge_r, lcolor, nivel, text_size=14)
        y = cy - badge_r - 12

        # Level phrase
        y = self._para(c, f"\u00ab{frase}\u00bb",
                        MARGIN + 25, y, CONTENT_W - 50,
                        _fn("i"), 9.5, TEAL, align=TA_CENTER)
        y -= 18
        return y

    def _section_desc(self, c, y, desc):
        """Level description with bullets. Returns y below."""
        # Title
        c.setFont(_fn("b"), 11)
        c.setFillColor(WHITE)
        c.drawString(MARGIN, y, "Descripci\u00f3n de tu nivel")
        y -= 5
        # Accent line
        c.setStrokeColor(ACCENT)
        c.setLineWidth(0.5)
        c.line(MARGIN, y, MARGIN + 160, y)
        y -= 12

        # Paragraph 1
        y = self._para(c, desc["parrafo1"], MARGIN, y, CONTENT_W,
                        _fn("r"), 9, LIGHT, align=TA_JUSTIFY)
        y -= 6

        # Bullets header
        if desc.get("bullets_header"):
            y = self._para(c, desc["bullets_header"], MARGIN, y, CONTENT_W,
                            _fn("b"), 9, LIGHT)
            y -= 3

        # Bullets
        for b in desc.get("bullets", []):
            y = self._para(c, f"\u2022  {b}", MARGIN + 14, y, CONTENT_W - 14,
                            _fn("r"), 8.5, LIGHT)
            y -= 2

        y -= 4
        # Paragraph 2
        y = self._para(c, desc["parrafo2"], MARGIN, y, CONTENT_W,
                        _fn("r"), 9, LIGHT, align=TA_JUSTIFY)
        y -= 8
        return y

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 2 — sections
    # ══════════════════════════════════════════════════════════════════════

    def _section_recs(self, c, y, recs):
        """Recommendations with numbered circles + optional image. Returns y."""
        # Title
        c.setFont(_fn("b"), 14)
        c.setFillColor(TEAL)
        c.drawString(MARGIN, y, "Recomendaciones para tu desarrollo")
        y -= 6
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.5)
        c.line(MARGIN, y, MARGIN + 240, y)
        y -= 20

        # Try to draw illustration on the right
        img_w = 155
        img_h = 210
        img_ok = False
        text_w = CONTENT_W
        if os.path.isfile(IMAGE_PATH):
            try:
                img_x = PAGE_W - MARGIN - img_w
                img_y = y - img_h
                c.drawImage(IMAGE_PATH, img_x, img_y,
                            width=img_w, height=img_h,
                            preserveAspectRatio=True)
                text_w = CONTENT_W - img_w - 15
                img_ok = True
            except Exception:
                pass

        img_bottom = y - img_h if img_ok else 0

        for idx, rec in enumerate(recs):
            # If past the image, use full width
            if img_ok and y < img_bottom + 10:
                text_w = CONTENT_W

            # Numbered circle
            cr = 11
            ccx = MARGIN + cr
            ccy = y - cr
            c.setFillColor(ACCENT)
            c.circle(ccx, ccy, cr, fill=1, stroke=0)
            c.setFont(_fn("b"), 11)
            c.setFillColor(WHITE)
            c.drawCentredString(ccx, ccy - 4, str(idx + 1))

            # Title
            tx = MARGIN + cr * 2 + 10
            c.setFont(_fn("b"), 10.5)
            c.setFillColor(WHITE)
            # Autofit title
            ttxt = rec["titulo"]
            avail_tw = text_w - (tx - MARGIN)
            tfs = 10.5
            while stringWidth(ttxt, _fn("b"), tfs) > avail_tw and tfs > 8:
                tfs -= 0.5
            c.setFont(_fn("b"), tfs)
            c.drawString(tx, y - 4, ttxt)
            y -= 20

            rec_x = tx
            rec_w = text_w - (tx - MARGIN)

            # Subtitle
            if rec.get("subtitulo"):
                y = self._para(c, rec["subtitulo"], rec_x, y, rec_w,
                                _fn("r"), 8.5, LIGHT)
                y -= 3

            # Body
            if rec.get("cuerpo"):
                y = self._para(c, rec["cuerpo"], rec_x, y, rec_w,
                                _fn("r"), 8.5, LIGHT, align=TA_JUSTIFY)
                y -= 3

            # Bullets
            for b in rec.get("bullets", []):
                y = self._para(c, f"\u2022  {b}", rec_x + 8, y, rec_w - 8,
                                _fn("r"), 8.5, LIGHT)
                y -= 2

            # Bold final
            if rec.get("bold_final"):
                y -= 1
                y = self._para(c, rec["bold_final"], rec_x, y, rec_w,
                                _fn("b"), 8.5, TEAL)

            y -= 18

        return y

    def _section_closing(self, c, y):
        """Closing message + inspirational quote. Returns y below."""
        y -= 8
        # Thin divider
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.4)
        c.line(MARGIN + 80, y, PAGE_W - MARGIN - 80, y)
        y -= 22

        # Message
        y = self._para(
            c,
            "Este resultado no te define; solo refleja c\u00f3mo "
            "gestionas hoy tus emociones.",
            MARGIN + 15, y, CONTENT_W - 30,
            _fn("r"), 9.5, LIGHT, align=TA_CENTER,
        )
        y -= 10

        # Quote
        y = self._para(
            c,
            "\u00abLa inteligencia emocional no es un rasgo fijo, "
            "es una habilidad entrenable.\u00bb",
            MARGIN + 15, y, CONTENT_W - 30,
            _fn("i"), 10.5, TEAL, align=TA_CENTER,
        )
        y -= 25

        # Branding
        c.setFont(_fn("b"), 8.5)
        c.setFillColor(ACCENT)
        c.drawCentredString(PAGE_W / 2, y, "skillera.com")
        return y - 15
