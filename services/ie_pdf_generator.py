"""
IE PDF Generator v4 — Template Overlay

Usa PyMuPDF (fitz) para superponer contenido dinámico sobre assets/template_ie.pdf.

El template ya contiene visualmente: header con gradiente, logo Skillera, título,
párrafo introductorio, sección ¿Qué es IE?, escala de valoración con badges,
separador, outline del badge de nivel, ilustración con bloques 1/2/3, CTA y footer.

Solo se generan dinámicamente: nombre, puesto, score, relleno del badge de nivel,
texto del nivel, frase, descripción y textos de las 3 recomendaciones.

Dimensiones reales del template: 1440.0 × 2557.5 pt
Coordenadas extraídas directamente del template (no escaladas).

Layout del template (sección Informe, y > 756):
  - LEFT COLUMN  (x: 0–560):  Badge orgánico, Nombre, Puesto, Badge nivel
  - RIGHT COLUMN (x: 560+):   Score, Frase, Descripción
  - FULL WIDTH   (y > 1430):  Rec circles+texto (x<790), Ilustración (x>798)

Coordenadas: (x, y) desde TOP-LEFT — convención PyMuPDF con Y creciendo hacia abajo.
"""

import os
from io import BytesIO

import fitz  # PyMuPDF


# ── Unicode → Latin-1 replacement map ─────────────────────────────────────────
# Base14 fonts (helv, hebo, hebi) only support Latin-1.
# Characters outside Latin-1 render as "?" — we map them to Latin-1 equivalents.
_UNICODE_MAP = {
    "\u201c": "\u00ab",   # " → «
    "\u201d": "\u00bb",   # " → »
    "\u2022": "\u00b7",   # • → ·  (middle dot, best Latin-1 bullet substitute)
}

def _sanitize(text: str) -> str:
    """Replace Unicode chars unsupported by Base14 fonts with Latin-1 equivalents."""
    for src, dst in _UNICODE_MAP.items():
        text = text.replace(src, dst)
    return text


# ── Paths ──────────────────────────────────────────────────────────────────────
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)
TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template_ie.pdf")


# ── Colores (RGB tuplas 0.0–1.0 para PyMuPDF) ─────────────────────────────────
C_WHITE    = (1.0,   1.0,   1.0)
C_LAVANDA2 = (0.702, 0.592, 1.0)    # #B397FF — frase Bajo/Medio
C_GRAY     = (0.627, 0.682, 0.753)  # #A0AEC0

NIVEL_FILL_COLOR = {
    "Alto":  (0.624, 0.478, 0.918),  # #9F7AEA — púrpura
    "Medio": (0.400, 0.494, 0.918),  # #667EEA — azul
    "Bajo":  (0.627, 0.682, 0.753),  # #A0AEC0 — gris
}

FRASE_COLOR = {
    "Alto":  C_WHITE,
    "Medio": C_LAVANDA2,
    "Bajo":  C_LAVANDA2,
}


# ── Coordenadas directas del template (1440 × 2557.5 pt) ─────────────────────
# Extraídas con page.get_text('dict'), get_images(), get_drawings().
#
# Template text elements de referencia:
#   "Nombre:"   (46.6, 857.1) – (193.5, 903.2)  font=33pt  white
#   "Puesto:"   (46.6, 902.1) – (171.1, 948.2)  font=33pt  white
#   "X puntos…" (637.7, 975.4) – (945.8, 1014.6) font=28pt white (placeholder)
#   Badge img   (-94.8, 839.5) – (559.6, 1493.9) 654×654
#   Rec circle1 (71.6, 1432.9) – (118.2, 1488.2) fill=lavanda
#   Rec circle2 (72.3, 1657.6) – (118.2, 1711.9) fill=lavanda
#   Rec circle3 (71.6, 1828.8) – (117.4, 1885.6) fill=lavanda
#   Illustration (798.3, 1432.9) – (1431.3, 2065.9)

# Nombre: justo después del label "Nombre:" que termina en x≈194
# baseline alineada con label (bbox top=857, font=33pt → baseline≈890)
NOMBRE_X  = 200
NOMBRE_Y  = 890

# Puesto: justo después del label "Puesto:" que termina en x≈171
# baseline alineada (bbox top=902, font=33pt → baseline≈935)
PUESTO_X  = 178
PUESTO_Y  = 935

# Score: centrado sobre el placeholder "X puntos de 40 puntos"
# Template text center x = (638+946)/2 ≈ 792,  baseline ≈ 1003
SCORE_CENTER_X = 792
SCORE_Y        = 1003

# Rect para redactar el placeholder "X puntos de 40 puntos" del template
SCORE_PLACEHOLDER_RECT = fitz.Rect(630, 970, 955, 1020)

# Badge fill: rounded rect dentro del badge orgánico
# Badge orgánico: (-95, 840) – (560, 1494).
# El fill va en la zona central-inferior del orgánico.
BADGE_X1 = 50
BADGE_Y1 = 1100
BADGE_X2 = 470
BADGE_Y2 = 1380

BADGE_CENTER_X = 260
BADGE_CENTER_Y = 1260

BADGE_RADIUS = 0.15  # fracción del lado menor (PyMuPDF: 0.0–1.0)

# Frase: columna derecha, debajo del score
FRASE_RECT = fitz.Rect(
    580, 1040,    # top-left
    1380, 1200,   # bottom-right
)

# Descripción: columna derecha, debajo de frase
DESC_RECT = fitz.Rect(
    580, 1200,
    1380, 1420,
)

# Recomendaciones: a la derecha de los círculos, izquierda de la ilustración
# Circle 1: (72, 1433)–(118, 1488)  number "1" at y≈1445–1475
# Circle 2: (72, 1658)–(118, 1712)  number "2" at y≈1669–1699
# Circle 3: (72, 1829)–(118, 1886)  number "3" at y≈1841–1873
REC_X1 = 135
REC_X2 = 780    # illustration starts at x=798

REC_ZONES = [
    fitz.Rect(REC_X1, 1433, REC_X2, 1640),
    fitz.Rect(REC_X1, 1658, REC_X2, 1815),
    fitz.Rect(REC_X1, 1829, REC_X2, 2060),
]

# ── Font sizes ────────────────────────────────────────────────────────────────
FS_NAME      = 24     # nombre y puesto (label es 33pt; valor un poco menor)
FS_SCORE     = 28     # igual que placeholder del template
FS_BADGE     = 40     # texto del nivel dentro del badge
FS_FRASE     = 20     # frase motivacional
FS_DESC      = 17     # descripción
FS_REC_TITLE = 16     # título de recomendación (bold)
FS_REC_BODY  = 15     # cuerpo de recomendación


# ── Textos estáticos por nivel ─────────────────────────────────────────────────
IE_CONTENT = {
    "Alto": {
        "frase": (
            "\u201cGestionas tus emociones con conciencia y "
            "eliges c\u00f3mo responder\u201d"
        ),
        "descripcion": (
            "Probablemente:\n"
            "\u2022 Reconoces lo que sientes y c\u00f3mo influye en tus decisiones.\n"
            "\u2022 Manejas conversaciones dif\u00edciles con equilibrio.\n"
            "\u2022 Utilizas el feedback como herramienta de crecimiento.\n"
            "\u2022 Influyes positivamente en el clima emocional de tu entorno."
        ),
        "recomendaciones": [
            (
                "Entrena la regulaci\u00f3n en alta intensidad\n"
                "Observa qu\u00e9 cambia bajo presi\u00f3n real (conflicto, jerarqu\u00eda). "
                "Ah\u00ed se mide el dominio."
            ),
            (
                "Desarrolla IE interpersonal\n"
                "Ayuda a otros a regularse. Valida emociones antes de "
                "proponer soluciones."
            ),
            (
                "Reflexiona sobre patrones invisibles\n"
                "Con alta IE a\u00fan existen puntos ciegos. Preg\u00fantate: "
                "\u00bfQu\u00e9 cr\u00edtica me incomoda? \u00bfD\u00f3nde pierdo neutralidad?"
            ),
        ],
    },
    "Medio": {
        "frase": (
            "\u201cReconoces lo que sientes, pero bajo presi\u00f3n "
            "vuelves a patrones autom\u00e1ticos\u201d"
        ),
        "descripcion": (
            "Tienes una base s\u00f3lida, pero la regulaci\u00f3n a\u00fan no es consistente.\n"
            "Es probable que escuches feedback pero te afecte m\u00e1s de lo que\n"
            "reconoces, o que bajo estr\u00e9s las buenas intenciones se debiliten."
        ),
        "recomendaciones": [
            (
                "Practica la regulaci\u00f3n antes de conversar\n"
                "Antes de una conversaci\u00f3n dif\u00edcil: \u00bfQu\u00e9 quiero lograr? "
                "\u00bfDesde qu\u00e9 emoci\u00f3n hablo?"
            ),
            (
                "Pide feedback sobre tu impacto emocional\n"
                "Pregunta a alguien de confianza c\u00f3mo te percibe bajo presi\u00f3n."
            ),
            (
                "Desarrolla vocabulario emocional m\u00e1s amplio\n"
                "Diferencia: frustrado, decepcionado, ansioso, inseguro. "
                "Mayor precisi\u00f3n = mejor regulaci\u00f3n."
            ),
        ],
    },
    "Bajo": {
        "frase": (
            "\u201cTus emociones suelen gestionarse de forma "
            "reactiva o evitativa\u201d"
        ),
        "descripcion": (
            "Hay poca conciencia emocional y alto impacto en tus decisiones.\n"
            "Es posible que reacciones impulsivamente o evites conversaciones\n"
            "inc\u00f3modas. Esto no habla de incapacidad, sino de bajo\n"
            "entrenamiento emocional consciente."
        ),
        "recomendaciones": [
            (
                "Entrena la identificaci\u00f3n emocional diaria\n"
                "Al final del d\u00eda: \u00bfQu\u00e9 sent\u00ed? \u00bfCu\u00e1ndo fue m\u00e1s intenso? "
                "\u00bfC\u00f3mo reaccion\u00e9? Nombrar la emoci\u00f3n reduce su intensidad."
            ),
            (
                "Introduce la pausa de 90 segundos\n"
                "Bajo tensi\u00f3n, respira profundo y retrasa tu reacci\u00f3n. "
                "Activa regulaci\u00f3n en lugar del impulso."
            ),
            (
                "Separa hecho de interpretaci\u00f3n\n"
                "Escribe una situaci\u00f3n y divide: Hecho / Lo que pens\u00e9 / "
                "Lo que sent\u00ed / Lo que hice."
            ),
        ],
    },
}


# ── Clase principal ────────────────────────────────────────────────────────────
class IEPDFGenerator:
    """
    Genera PDFs de IE superponiendo contenido dinámico sobre template_ie.pdf.
    Usa únicamente PyMuPDF (fitz). Sin ReportLab.
    """

    def generate(
        self,
        name: str,
        position: str,
        total_score: float,
        nivel: str,
    ) -> BytesIO:
        content = IE_CONTENT[nivel]

        doc = fitz.open(TEMPLATE_PATH)
        page = doc[0]

        # 1. Redactar el placeholder "X puntos de 40 puntos" del template
        self._redact_score_placeholder(page)

        # 2. Dibujar contenido dinámico (sanitizar Unicode → Latin-1)
        self._draw_informe_block(page, name, position, total_score, nivel)
        self._draw_frase(page, nivel, _sanitize(content["frase"]))
        self._draw_descripcion(page, _sanitize(content["descripcion"]))
        self._draw_recomendaciones(page, [_sanitize(r) for r in content["recomendaciones"]])

        buffer = BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        return buffer

    # ── Redacción del placeholder ─────────────────────────────────────────
    @staticmethod
    def _redact_score_placeholder(page):
        """Elimina el texto placeholder 'X puntos de 40 puntos' del template."""
        ann = page.add_redact_annot(SCORE_PLACEHOLDER_RECT)
        ann.set_colors(fill=None)   # sin relleno → mantiene imagen de fondo
        ann.update()
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    # ── Bloque Informe ────────────────────────────────────────────────────
    def _draw_informe_block(
        self, page, name, position, total_score, nivel
    ):
        # Nombre (después de "Nombre:" label)
        page.insert_text(
            (NOMBRE_X, NOMBRE_Y), name,
            fontname="helv", fontsize=FS_NAME, color=C_WHITE,
        )
        # Puesto (después de "Puesto:" label)
        page.insert_text(
            (PUESTO_X, PUESTO_Y), position,
            fontname="helv", fontsize=FS_NAME, color=C_WHITE,
        )
        # Score centrado sobre el área del placeholder redactado
        score_text = f"{int(total_score)} puntos de 40 puntos"
        text_len = fitz.get_text_length(
            score_text, fontname="helv", fontsize=FS_SCORE
        )
        page.insert_text(
            (SCORE_CENTER_X - text_len / 2, SCORE_Y), score_text,
            fontname="helv", fontsize=FS_SCORE, color=C_WHITE,
        )
        # Badge relleno (rounded rectangle)
        badge_rect = fitz.Rect(BADGE_X1, BADGE_Y1, BADGE_X2, BADGE_Y2)
        page.draw_rect(
            badge_rect,
            color=None,
            fill=NIVEL_FILL_COLOR[nivel],
            radius=BADGE_RADIUS,
        )
        # Texto del nivel centrado en el badge
        nivel_len = fitz.get_text_length(
            nivel, fontname="hebo", fontsize=FS_BADGE
        )
        page.insert_text(
            (BADGE_CENTER_X - nivel_len / 2, BADGE_CENTER_Y), nivel,
            fontname="hebo", fontsize=FS_BADGE, color=C_WHITE,
        )

    # ── Frase motivacional ────────────────────────────────────────────────
    def _draw_frase(self, page, nivel, frase):
        page.insert_textbox(
            FRASE_RECT, frase,
            fontname="hebi", fontsize=FS_FRASE,
            color=FRASE_COLOR[nivel], align=fitz.TEXT_ALIGN_LEFT,
        )

    # ── Descripción ───────────────────────────────────────────────────────
    def _draw_descripcion(self, page, texto):
        page.insert_textbox(
            DESC_RECT, texto,
            fontname="helv", fontsize=FS_DESC,
            color=C_WHITE, align=fitz.TEXT_ALIGN_LEFT,
        )

    # ── Recomendaciones ───────────────────────────────────────────────────
    def _draw_recomendaciones(self, page, recomendaciones):
        for rec_text, zone in zip(recomendaciones, REC_ZONES):
            titulo, *resto = rec_text.split("\n", 1)
            cuerpo = resto[0] if resto else ""

            # Título bold — baseline a 20pt del top de la zona
            page.insert_text(
                (zone.x0, zone.y0 + 20), titulo,
                fontname="hebo", fontsize=FS_REC_TITLE, color=C_WHITE,
            )
            # Cuerpo regular — debajo del título
            if cuerpo:
                body_rect = fitz.Rect(
                    zone.x0, zone.y0 + 30,
                    zone.x1, zone.y1,
                )
                page.insert_textbox(
                    body_rect, cuerpo,
                    fontname="helv", fontsize=FS_REC_BODY,
                    color=C_WHITE, align=fitz.TEXT_ALIGN_LEFT,
                )
