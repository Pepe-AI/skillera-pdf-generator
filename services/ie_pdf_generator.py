"""
IE PDF Generator v3 — Alta fidelidad al template original
Reconstruido con coordenadas y colores exactos extraídos del PDF vectorial.

Dimensiones originales: 1440 x 2557.5 pt → escalado a A4 (595 x 842 pt)
Scale factors: x=0.4132, y=0.3292

Paleta exacta extraída:
  Gradiente header: #5735b1 (top) → #120931 (y≈263pt from top) → #000000 (body)
  Teal:    #3ccbb2  — labels ¿Qué es IE?, separador
  Lavanda: #d8c9ff  — label "Escala de valoración"
  Lavanda2:#b397ff  — badge rec circles, CTA title, frase Bajo/Medio
  Blanco:  #ffffff  — texto principal
  Naranja: —        — solo frase Alt (blanco)
"""

import math
from io import BytesIO
from datetime import date
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ASSETS_DIR — resolved relative to the project root (one level up from services/)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# ── Paleta exacta ──────────────────────────────────────────────────────────────
C_WHITE    = HexColor("#FFFFFF")
C_TEAL     = HexColor("#3CCBB2")       # ¿Qué es IE?, separador
C_LAVANDA  = HexColor("#D8C9FF")       # label Escala
C_LAVANDA2 = HexColor("#B397FF")       # circles rec, CTA title, frase Bajo/Medio
C_GRAY     = HexColor("#A0AEC0")       # texto secundario
C_BLACK    = HexColor("#000000")
C_HDR_TOP  = HexColor("#5735B1")       # header gradiente top
C_HDR_MID  = HexColor("#3A1E8A")       # header gradiente mid
C_HDR_BOT  = HexColor("#120931")       # header/body transition
C_BODY_BG  = HexColor("#080520")       # fondo body (muy oscuro)

# Color frase por nivel
FRASE_COLOR = {
    "Alto":  C_WHITE,
    "Medio": C_LAVANDA2,
    "Bajo":  C_LAVANDA2,
}

# ── Textos estáticos ───────────────────────────────────────────────────────────
IE_CONTENT = {
    "Alto": {
        "frase": "\u201cGestionas tus emociones con conciencia y eliges c\u00f3mo responder\u201d",
        "intro": None,
        "bullets_label": "Probablemente:",
        "bullets": [
            "Reconoces lo que sientes y c\u00f3mo influye en tus decisiones.",
            "Manejas conversaciones dif\u00edciles con equilibrio.",
            "Utilizas el feedback como herramienta de crecimiento.",
            "Influyes positivamente en el clima emocional de tu entorno.",
        ],
        "cierre": (
            "El reto en este nivel no es aprender lo b\u00e1sico, sino "
            "<b>sostener la habilidad bajo alta carga emocional y liderazgo de otros.</b>"
        ),
        "titulo_rec": "Recomendaciones:",
        "recomendaciones": [
            {
                "titulo": "Entrena la regulaci\u00f3n en situaciones de alta intensidad",
                "cuerpo": "Observa qu\u00e9 cambia cuando hay presi\u00f3n real (tiempo, conflicto, jerarqu\u00eda). <b>Ah\u00ed se mide el dominio.</b>",
                "sub_bullets": [],
            },
            {
                "titulo": "Desarrolla inteligencia emocional interpersonal",
                "cuerpo": "No solo gestiones tus emociones; ayuda a otros a regularse. <b>Practica validar emociones antes de proponer soluciones.</b>",
                "sub_bullets": [],
            },
            {
                "titulo": "Reflexiona sobre tus patrones invisibles",
                "cuerpo": "Incluso con alta inteligencia emocional, existen sesgos o puntos ciegos. Preg\u00fantate:",
                "sub_bullets": [
                    "\u00bfQu\u00e9 tipo de cr\u00edtica a\u00fan me incomoda?",
                    "\u00bfEn qu\u00e9 situaciones pierdo m\u00e1s neutralidad?",
                ],
            },
        ],
    },
    "Medio": {
        "frase": "\u201cReconoces lo que sientes, pero bajo presi\u00f3n vuelves a patrones autom\u00e1ticos\u201d.",
        "intro": (
            "<b>Tienes una base s\u00f3lida para desarrollar mayor regulaci\u00f3n emocional.</b> "
            "Hay conciencia, pero la regulaci\u00f3n todav\u00eda no es consistente."
        ),
        "bullets_label": "Es probable que:",
        "bullets": [
            "Escuches feedback, pero te afecte m\u00e1s de lo que reconoces.",
            "Identifiques emociones, pero no siempre sepas gestionarlas.",
            "Tengas buenas intenciones relacionales, aunque bajo estr\u00e9s se debiliten.",
        ],
        "cierre": (
            "Este <b>nivel es una base s\u00f3lida.</b> La diferencia entre nivel "
            "<b>medio y alto</b> suele estar en la consistencia, especialmente en momentos de tensi\u00f3n."
        ),
        "titulo_rec": "Recomendaciones para potenciar tu desarrollo:",
        "recomendaciones": [
            {
                "titulo": "Practica la regulaci\u00f3n antes de conversar",
                "cuerpo": "Antes de una conversaci\u00f3n dif\u00edcil, preg\u00fantate:",
                "sub_bullets": [
                    "\u00bfQu\u00e9 quiero lograr?",
                    "\u00bfDesde qu\u00e9 emoci\u00f3n estoy hablando?",
                    "<b>Esto aumenta la intenci\u00f3n consciente.</b>",
                ],
            },
            {
                "titulo": "Pide feedback sobre tu impacto emocional",
                "cuerpo": "Pregunta a alguien de confianza:",
                "sub_bullets": [
                    "\u201cCuando estoy bajo presi\u00f3n, \u00bfc\u00f3mo me percibes?\u201d",
                    "<b>La autoconciencia se fortalece con retroalimentaci\u00f3n externa.</b>",
                ],
            },
            {
                "titulo": "Desarrolla vocabulario emocional m\u00e1s amplio",
                "cuerpo": (
                    "No es solo \u201cmolesto\u201d o \u201cbien\u201d, practica diferenciar: frustrado, "
                    "decepcionado, ansioso, inseguro, exigente, etc. "
                    "<b>Mayor precisi\u00f3n = mejor regulaci\u00f3n.</b>"
                ),
                "sub_bullets": [],
            },
        ],
    },
    "Bajo": {
        "frase": "\u201cTus emociones suelen gestionarse de forma reactiva o evitativa\u201d.",
        "intro": (
            "Hay poca conciencia emocional y alto impacto en decisiones y relaciones. "
            "Tiendes a reaccionar de forma autom\u00e1tica frente a tus emociones, especialmente "
            "bajo presi\u00f3n o conflicto. Puede haber dificultad para identificar con claridad "
            "lo que sientes o para regularlo antes de actuar."
        ),
        "bullets_label": "Es posible que:",
        "bullets": [
            "Reacciones impulsivamente o evites conversaciones inc\u00f3modas.",
            "Te cueste separar el hecho de la emoci\u00f3n.",
            "Las emociones influyan en tus decisiones sin que lo notes plenamente.",
            "Haya impacto frecuente en relaciones laborales o personales.",
        ],
        "cierre": (
            "Este nivel no habla de incapacidad, sino de bajo entrenamiento emocional "
            "consciente. Muchas personas operan desde este punto sin haber desarrollado "
            "herramientas formales de regulaci\u00f3n."
        ),
        "titulo_rec": "Recomendaciones para potenciar tu desarrollo:",
        "recomendaciones": [
            {
                "titulo": "Entrena la identificaci\u00f3n emocional diaria",
                "cuerpo": "Al final del d\u00eda preg\u00fantate:",
                "sub_bullets": [
                    "\u00bfQu\u00e9 sent\u00ed hoy?",
                    "\u00bfEn qu\u00e9 momento fue m\u00e1s intenso?",
                    "\u00bfC\u00f3mo reaccion\u00e9?",
                    "<b>Nombrar la emoci\u00f3n reduce su intensidad.</b>",
                ],
            },
            {
                "titulo": "Introduce la pausa de 90 segundos",
                "cuerpo": (
                    "Antes de responder en situaciones tensas, respira profundo y retrasa tu "
                    "reacci\u00f3n al menos 90 segundos. Esto activa la regulaci\u00f3n en lugar del impulso."
                ),
                "sub_bullets": [],
            },
            {
                "titulo": "Separa hecho de interpretaci\u00f3n",
                "cuerpo": "Escribe una situaci\u00f3n reciente y div\u00eddela en:",
                "sub_bullets": [
                    "Hecho objetivo",
                    "Lo que pens\u00e9",
                    "Lo que sent\u00ed",
                    "Lo que hice",
                    "<b>Esto desarrolla conciencia y rompe la reacci\u00f3n autom\u00e1tica.</b>",
                ],
            },
        ],
    },
}


# ── helpers de layout ──────────────────────────────────────────────────────────
def _para(text, font="Helvetica", size=8, color=None, leading=11,
          align=TA_JUSTIFY, left_indent=0):
    color = color or C_WHITE
    return Paragraph(text, ParagraphStyle(
        "_", fontName=font, fontSize=size, textColor=color,
        leading=leading, alignment=align, leftIndent=left_indent,
        spaceAfter=0, spaceBefore=0))


def _draw_para(c, x, y, text, width, **kwargs):
    """Dibuja párrafo en (x,y) donde y es la coordenada SUPERIOR del texto."""
    p = _para(text, **kwargs)
    pw, ph = p.wrap(width, 9999)
    p.drawOn(c, x, y - ph)
    return y - ph  # nueva y (parte inferior del texto)


# ── Gradiente de fondo ─────────────────────────────────────────────────────────
def draw_gradient_bg(c: canvas.Canvas, page_w: float, page_h: float):
    """
    Simula el gradiente vertical del template:
    top → #5735b1 oscureciendo hasta #000000 en el 31% inferior.
    Usa bandas horizontales estrechas (1pt) para aproximar el gradiente.
    """
    # Gradiente en el header (~top 31% = 263pt)
    header_h = 263
    steps = header_h  # 1 banda por punto

    # Colores de inicio y fin del gradiente (RGB 0-1)
    r0, g0, b0 = 0x57/255, 0x35/255, 0xb1/255  # #5735b1
    r1, g1, b1 = 0x12/255, 0x09/255, 0x31/255  # #120931

    for i in range(steps):
        t = i / steps
        r = r0 + (r1 - r0) * t
        g = g0 + (g1 - g0) * t
        b = b0 + (b1 - b0) * t
        y_rect = page_h - i - 1
        c.setFillColorRGB(r, g, b)
        c.rect(0, y_rect, page_w, 1, fill=1, stroke=0)

    # Body: fondo muy oscuro (casi negro)
    body_y = 0
    body_h = page_h - header_h
    c.setFillColor(HexColor("#08052A"))
    c.rect(0, 0, page_w, body_h, fill=1, stroke=0)


# ── Clase principal ────────────────────────────────────────────────────────────
class IEPDFGenerator:
    """
    Genera PDFs de IE con fidelidad máxima al template original.

    Diseño: gradiente púrpura en header (top ~31%) + fondo oscuro en body.
    Layout de una sola página A4 (595 x 842 pt).
    """

    W, H = A4   # 595.28 × 841.89
    ML = 17     # margin left (≈ 42/1440 * 595)
    MR = 17     # margin right
    CW = W - ML - MR  # content width ≈ 561

    # Constantes de layout (en pts A4, calculadas de coordenadas originales)
    HEADER_H    = 245   # altura zona header (gradiente)
    FOOTER_H    =  52   # altura zona footer
    Y_MIN       =  FOOTER_H + 2  # buffer mínimo

    def generate(self, name: str, position: str,
                 total_score: float, nivel: str) -> BytesIO:
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        content = IE_CONTENT[nivel]

        draw_gradient_bg(c, self.W, self.H)

        # ── HEADER ────────────────────────────────────────────────────────────
        self._draw_logo(c)
        self._draw_title(c)
        self._draw_intro_para(c)
        self._draw_que_es_ie(c)
        self._draw_escala(c)
        self._draw_separator(c)

        # ── BODY ──────────────────────────────────────────────────────────────
        y = self.H - self.HEADER_H  # cursor empieza justo debajo del header

        y = self._draw_informe_title(c, y)
        y = self._draw_user_score(c, y, name, position, total_score)
        y = self._draw_badge(c, y, nivel)
        y = self._draw_frase(c, y, nivel, content)
        y = self._draw_descripcion(c, y, content)
        y = self._draw_recomendaciones(c, y, content)
        self._draw_cta(c, y)
        self._draw_footer(c)

        c.save()
        buf.seek(0)
        return buf

    # ── HEADER SECTIONS ───────────────────────────────────────────────────────

    def _draw_logo(self, c):
        """Logo arriba a la derecha en zona del header."""
        logo_h, logo_w = 22, 65
        logo_x = self.W - self.MR - logo_w
        logo_y = self.H - 28 - logo_h  # 28pt desde top
        try:
            path = os.path.join(ASSETS_DIR, "logo_transparent.png")
            c.drawImage(ImageReader(path), logo_x, logo_y,
                        width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(self.W - self.MR, logo_y + 6, "\u2736 Skillera")

    def _draw_title(self, c):
        """Título principal: 'Diagnóstico / Inteligencia Emocional'."""
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 19)
        c.drawString(self.ML, self.H - 51, "Diagn\u00f3stico")
        c.setFont("Helvetica-Bold", 26)
        c.drawString(self.ML, self.H - 74, "Inteligencia Emocional")

    def _draw_intro_para(self, c):
        """Párrafo de introducción."""
        intro = (
            "El presente instrumento tiene como finalidad ofrecer una referencia sobre ciertos "
            "aspectos relacionados con la inteligencia emocional. Es importante considerar que "
            "los resultados obtenidos no deben interpretarse de manera negativa ni como una "
            "etiqueta definitiva, sino como una oportunidad para reflexionar, identificar "
            "\u00e1reas de mejora y fortalecer habilidades personales."
        )
        _draw_para(c, self.ML, self.H - 100, intro, self.CW,
                   font="Helvetica", size=6.5, color=C_WHITE,
                   leading=9.5, align=TA_JUSTIFY)

    def _draw_que_es_ie(self, c):
        """Columna izquierda: ¿Qué es IE? + definición."""
        y_label = self.H - 148
        col_w = self.CW * 0.46

        c.setFillColor(C_TEAL)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.ML, y_label, "\u00bfQu\u00e9 es inteligencia emocional?")

        definicion = (
            "\u201cEs la capacidad de reconocer, comprender y gestionar las propias emociones, "
            "as\u00ed como influir positivamente en las de los dem\u00e1s, favoreciendo decisiones "
            "conscientes, relaciones saludables y un manejo equilibrado de las situaciones\u201d."
        )
        y_def = _draw_para(c, self.ML, y_label - 10, definicion, col_w,
                           font="Helvetica", size=6.5, color=C_WHITE,
                           leading=9.5, align=TA_JUSTIFY)

        frase = "<b>La inteligencia emocional es una competencia que puede desarrollarse con pr\u00e1ctica, conciencia y compromiso.</b>"
        _draw_para(c, self.ML, y_def - 4, frase, col_w,
                   font="Helvetica-Bold", size=6.5, color=C_TEAL,
                   leading=9.5, align=TA_JUSTIFY)

    def _draw_escala(self, c):
        """Columna derecha: Escala de valoración con 3 badges."""
        col2_x = self.CW * 0.52 + self.ML

        # Label
        c.setFillColor(C_LAVANDA)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(col2_x, self.H - 148, "Escala de valoraci\u00f3n")

        # Tres badges orgánicos de escala
        badge_r = 16
        badge_data = [
            ("Bajo",  col2_x + badge_r + 4,      self.H - 170),
            ("Medio", col2_x + badge_r*3 + 36,   self.H - 170),
            ("Alto",  col2_x + badge_r*5 + 68,   self.H - 170),
        ]
        ranges = {"Bajo": "10\u201320", "Medio": "21\u201330", "Alto": "31\u201340"}

        for label, bx, by in badge_data:
            self._draw_scale_badge(c, bx, by, badge_r, label)
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(bx, by - badge_r - 8, label)
            c.setFont("Helvetica", 5.5)
            c.drawCentredString(bx, by - badge_r - 17, f"{ranges[label]} puntos")

    def _draw_scale_badge(self, c, cx, cy, r, nivel):
        """Badge pequeño para la escala de valoración (dibujado vectorialmente)."""
        n = 7  # 7 lóbulos como en el template
        jitter = [0, 0.08, -0.06, 0.09, -0.07, 0.06, -0.08,
                  0, 0.07, -0.05, 0.08, -0.06, 0.05, -0.09]
        fill = HexColor("#4828AA")
        border = HexColor("#7355CC")

        for scale, color in [(1.0, border), (0.88, fill)]:
            pts = []
            for i in range(n * 2):
                ang = math.pi/2 + i * math.pi/n + jitter[i % len(jitter)]
                rad = (r * scale) if i % 2 == 0 else (r * 0.80 * scale)
                pts.append((cx + rad*math.cos(ang), cy + rad*math.sin(ang)))

            path = c.beginPath()
            path.moveTo(pts[0][0], pts[0][1])
            for i in range(1, len(pts)):
                p, q = pts[i-1], pts[i]
                mx, my = (p[0]+q[0])/2, (p[1]+q[1])/2
                path.curveTo(p[0], p[1], mx, my, q[0], q[1])
            path.close()
            c.saveState()
            c.setFillColor(color)
            c.drawPath(path, fill=1, stroke=0)
            c.restoreState()

        # Label text
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", max(5, r*0.4))
        c.drawCentredString(cx, cy - r*0.18, nivel)

    def _draw_separator(self, c):
        """Línea separadora teal entre header y body."""
        sep_y = self.H - self.HEADER_H + 2
        c.setStrokeColor(C_TEAL)
        c.setLineWidth(1.2)
        c.line(0, sep_y, self.W, sep_y)

    # ── BODY SECTIONS ─────────────────────────────────────────────────────────

    def _draw_informe_title(self, c, y):
        """'Informe Integrado de Resultados:' con estilo grande."""
        y -= 18
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.ML, y, "Informe Integrado de Resultados:")
        return y - 4

    def _draw_user_score(self, c, y, name, position, score):
        """Nombre, Puesto y Score."""
        # Nombre
        y -= 14
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.ML, y, "Nombre:")
        c.setFont("Helvetica", 9)
        c.drawString(self.ML + 46, y, name)

        # Puesto
        y -= 12
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.ML, y, "Puesto:")
        c.setFont("Helvetica", 9)
        c.drawString(self.ML + 44, y, position)

        # Score centrado
        y -= 18
        score_txt = f"<b>{int(score)} puntos de 40 puntos</b>"
        _draw_para(c, self.ML, y, score_txt, self.CW,
                   font="Helvetica-Bold", size=10, color=C_WHITE,
                   leading=14, align=TA_CENTER)
        return y - 10

    def _draw_badge(self, c, y, nivel):
        """Badge orgánico PNG del nivel (imagen embebida del template)."""
        y -= 4
        badge_size = 72  # tamaño en pts
        badge_x = self.ML + 2
        badge_y = y - badge_size

        # Intentar usar el badge PNG extraído del template
        badge_path = os.path.join(ASSETS_DIR, "badge_organico.png")
        try:
            c.drawImage(ImageReader(badge_path),
                        badge_x, badge_y,
                        width=badge_size, height=badge_size,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            # Fallback: dibujar vectorialmente
            cx = badge_x + badge_size / 2
            cy = badge_y + badge_size / 2
            r = badge_size / 2 - 4
            self._draw_fallback_badge(c, cx, cy, r)

        # Texto del nivel encima del badge
        badge_cx = badge_x + badge_size / 2
        badge_cy = badge_y + badge_size / 2
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(badge_cx, badge_cy - 5, nivel)

        return badge_y - 8

    def _draw_fallback_badge(self, c, cx, cy, r):
        """Badge vectorial de respaldo si no hay PNG."""
        n = 8
        jitter = [0, 0.06, -0.04, 0.08, -0.06, 0.04, -0.08, 0.05,
                  0, -0.05, 0.07, -0.03, 0.06, -0.07, 0.04, -0.06]
        for scale, color in [(1.0, HexColor("#3A1D86")), (0.88, HexColor("#1C0D4A"))]:
            pts = []
            for i in range(n*2):
                ang = math.pi/2 + i*math.pi/n + jitter[i % len(jitter)]
                rad = (r*scale) if i%2==0 else (r*0.82*scale)
                pts.append((cx + rad*math.cos(ang), cy + rad*math.sin(ang)))
            path = c.beginPath()
            path.moveTo(pts[0][0], pts[0][1])
            for i in range(1, len(pts)):
                p, q = pts[i-1], pts[i]
                mx, my = (p[0]+q[0])/2, (p[1]+q[1])/2
                path.curveTo(p[0], p[1], mx, my, q[0], q[1])
            path.close()
            c.saveState()
            c.setFillColor(color)
            c.drawPath(path, fill=1, stroke=0)
            c.restoreState()

    def _draw_frase(self, c, y, nivel, content):
        """Frase destacada del nivel."""
        y -= 6
        color = FRASE_COLOR[nivel]
        y = _draw_para(c, self.ML, y, content["frase"], self.CW,
                       font="Helvetica-BoldOblique", size=9.5,
                       color=color, leading=13, align=TA_LEFT)
        return y - 5

    def _draw_descripcion(self, c, y, content):
        """Descripción, bullets y cierre del nivel."""
        if content["intro"]:
            y = _draw_para(c, self.ML, y, content["intro"], self.CW,
                           font="Helvetica", size=7.5, color=C_WHITE,
                           leading=11, align=TA_JUSTIFY)
            y -= 4

        if content["bullets"]:
            c.setFillColor(HexColor("#D8C9FF"))
            c.setFont("Helvetica", 7.5)
            c.drawString(self.ML, y, content["bullets_label"])
            y -= 10

            for bullet in content["bullets"]:
                y = _draw_para(c, self.ML, y, f"\u2022\u2002{bullet}", self.CW,
                               font="Helvetica", size=7, color=C_WHITE,
                               leading=10, align=TA_LEFT, left_indent=8)
                y -= 1
            y -= 3

        if content["cierre"]:
            y = _draw_para(c, self.ML, y, content["cierre"], self.CW,
                           font="Helvetica", size=7.5, color=C_WHITE,
                           leading=11, align=TA_JUSTIFY)
            y -= 5

        return y

    def _draw_recomendaciones(self, c, y, content):
        """3 recomendaciones con badges numerados círculo + ilustración derecha."""
        # Título
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.ML, y, content["titulo_rec"])
        y -= 10

        ilus_w = 125
        ilus_x = self.W - self.MR - ilus_w
        text_w = ilus_x - self.ML - 6
        rec_start_y = y

        for i, rec in enumerate(content["recomendaciones"], 1):
            # Círculo badge número con color lavanda
            badge_r_small = 8
            bcx = self.ML + badge_r_small + 1
            bcy = y - badge_r_small - 1
            c.setFillColor(C_LAVANDA2)
            c.circle(bcx, bcy, badge_r_small, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(bcx, bcy - 2.5, str(i))

            # Título
            tx = self.ML + badge_r_small*2 + 5
            y_t = _draw_para(c, tx, y, rec["titulo"], text_w - badge_r_small*2 - 5,
                             font="Helvetica-Bold", size=7.5,
                             color=C_WHITE, leading=10)
            y = y_t - 2

            # Cuerpo
            if rec["cuerpo"]:
                y = _draw_para(c, tx, y, rec["cuerpo"], text_w - badge_r_small*2 - 5,
                               font="Helvetica", size=7,
                               color=HexColor("#D8C9FF"), leading=10)
                y -= 1

            # Sub-bullets
            for sb in rec["sub_bullets"]:
                y = _draw_para(c, tx + 8, y, f"\u2022\u2002{sb}",
                               text_w - badge_r_small*2 - 13,
                               font="Helvetica", size=6.8,
                               color=HexColor("#D8C9FF"), leading=10)
                y -= 1

            y -= 4  # espacio entre recomendaciones

        # Ilustración bloques (a la derecha de las recs)
        try:
            path = os.path.join(ASSETS_DIR, "image_bloques.jpeg")
            ilus_h = min(rec_start_y - y + 8, 145)
            ilus_bottom = max(y + 4, self.Y_MIN + 30)
            c.drawImage(ImageReader(path),
                        ilus_x, ilus_bottom,
                        width=ilus_w, height=ilus_h,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

        return y - 2

    def _draw_cta(self, c, y):
        """CTA centrado al final del body."""
        y -= 4
        # "¡Desbloquea tu potencial con la ayuda de expertos!"
        c.setFillColor(C_LAVANDA2)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(self.W / 2, y, "\u00a1Desbloquea tu potencial con la ayuda de expertos!")
        y -= 13

        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.W / 2, y,
                            "Solicita una sesi\u00f3n hoy mismo y empieza a avanzar en tu camino hacia el \u00e9xito.")
        y -= 11
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(self.W / 2, y, "\u00a1El cambio que est\u00e1s buscando est\u00e1 a solo un paso!")

    def _draw_footer(self, c):
        """Footer: logo izquierda + redes centro + contacto derecha."""
        fy = self.FOOTER_H - 10

        # Separador muy sutil
        c.setStrokeColor(HexColor("#3A3A3A"))
        c.setLineWidth(0.5)
        c.line(self.ML, fy + 32, self.W - self.MR, fy + 32)

        # Logo
        try:
            path = os.path.join(ASSETS_DIR, "logo_transparent.png")
            c.drawImage(ImageReader(path), self.ML, fy + 8,
                        width=50, height=17,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(self.ML, fy + 14, "\u2736 Skillera")

        # Redes sociales
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 7)
        c.drawCentredString(self.W/2, fy + 20, "f   \u0040   in")
        c.setFont("Helvetica", 6)
        c.drawCentredString(self.W/2, fy + 10, "skillera.transformacion")

        # Contacto
        c.setFont("Helvetica", 7)
        c.drawRightString(self.W - self.MR, fy + 20, "52 55 1958 9499")
        c.drawRightString(self.W - self.MR, fy + 10, "contacto@skillera.mx")

        # Legal (mínimo)
        legal = ("Este test es desarrollado por SKILLERA en colaboraci\u00f3n con Integra.Soulutions, "
                 "bajo la direcci\u00f3n y autor\u00eda de Nora Siqueros Cerda, Lic. en Psicolog\u00eda C\u00e9dula 4934789.")
        c.setFillColor(C_GRAY)
        c.setFont("Helvetica", 3.8)
        c.drawCentredString(self.W/2, 4, legal)
