"""
IE PDF Generator — Diagnóstico Inteligencia Emocional
Genera PDFs usando ReportLab overlay sobre template base con pypdf merge.
"""

import os
from io import BytesIO

import pypdf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph

from config import Config   # usa ASSETS_DIR


# ── Constantes de página ──────────────────────────────────────────────────
PAGE_W = 630.0
PAGE_H = 1092.0


def fitz_to_rl(fitz_y: float) -> float:
    """Convierte coordenada Y de sistema fitz (top-left) a ReportLab (bottom-left)."""
    return PAGE_H - fitz_y


# ── Contenido estático por nivel ──────────────────────────────────────────
IE_CONTENT = {
    "Bajo": {
        "frase": '\u201cTus emociones suelen gestionarse de forma reactiva o evitativa\u201d.',
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
                    "tu reacci\u00f3n al menos 90 segundos. Esto activa la regulaci\u00f3n en lugar del impulso."
                ),
            },
            {
                "titulo": "Separa hecho de interpretaci\u00f3n",
                "subtitulo": "Escribe una situaci\u00f3n reciente y div\u00eddela en:",
                "bullets": ["Hecho objetivo", "Lo que pens\u00e9", "Lo que sent\u00ed", "Lo que hice"],
                "bold_final": "Esto desarrolla conciencia y rompe la reacci\u00f3n autom\u00e1tica.",
            },
        ],
    },
    "Medio": {
        "frase": '\u201cReconoces lo que sientes, pero bajo presi\u00f3n vuelves a patrones autom\u00e1ticos\u201d.',
        "descripcion": {
            "parrafo1": (
                "Reconoces lo que sientes, pero bajo presi\u00f3n vuelves a patrones autom\u00e1ticos. "
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
                "Este nivel es una base s\u00f3lida. La diferencia entre nivel medio y alto suele "
                "estar en la consistencia, especialmente en momentos de tensi\u00f3n."
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
                "bullets": ['\u201cCuando estoy bajo presi\u00f3n, \u00bfc\u00f3mo me percibes?\u201d'],
                "bold_final": "La autoconciencia se fortalece con retroalimentaci\u00f3n externa.",
            },
            {
                "titulo": "Desarrolla vocabulario emocional m\u00e1s amplio",
                "cuerpo": (
                    'No es solo \u201cmolesto\u201d o \u201cbien\u201d, practica diferenciar: frustrado, '
                    "decepcionado, ansioso, inseguro, exigente, etc."
                ),
                "bold_final": "Mayor precisi\u00f3n = mejor regulaci\u00f3n.",
            },
        ],
    },
    "Alto": {
        "frase": '\u201cGestionas tus emociones con conciencia y eliges c\u00f3mo responder\u201d.',
        "descripcion": {
            "parrafo1": "Gestionas tus emociones con conciencia y eliges c\u00f3mo responder. Probablemente:",
            "bullets_header": None,
            "bullets": [
                "Reconoces lo que sientes y c\u00f3mo influye en tus decisiones.",
                "Manejas conversaciones dif\u00edciles con equilibrio.",
                "Utilizas el feedback como herramienta de crecimiento.",
                "Influyes positivamente en el clima emocional de tu entorno.",
            ],
            "parrafo2": (
                "El reto en este nivel no es aprender lo b\u00e1sico, sino sostener la habilidad "
                "bajo alta carga emocional y liderazgo de otros."
            ),
        },
        "recs": [
            {
                "titulo": "Entrena la regulaci\u00f3n en situaciones de alta intensidad",
                "cuerpo": "Observa qu\u00e9 cambia cuando hay presi\u00f3n real (tiempo, conflicto, jerarqu\u00eda).",
                "bold_final": "Ah\u00ed se mide el dominio.",
            },
            {
                "titulo": "Desarrolla inteligencia emocional interpersonal",
                "cuerpo": "No solo gestiones tus emociones; ayuda a otros a regularse.",
                "bold_final": "Practica validar emociones antes de proponer soluciones.",
            },
            {
                "titulo": "Reflexiona sobre tus patrones invisibles",
                "subtitulo": (
                    "Incluso con alta inteligencia emocional, existen sesgos o puntos ciegos. "
                    "Preg\u00fantate:"
                ),
                "bullets": [
                    "\u00bfQu\u00e9 tipo de cr\u00edtica a\u00fan me incomoda?",
                    "\u00bfEn qu\u00e9 situaciones pierdo m\u00e1s neutralidad?",
                ],
            },
        ],
    },
}

# ── Colores ────────────────────────────────────────────────────────────────
C_WHITE  = HexColor("#FFFFFF")
C_TEAL   = HexColor("#3CCBB2")   # frase del nivel


class IEPDFGenerator:
    """Genera PDFs del Diagnóstico IE con overlay sobre template base."""

    TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "Template_para_todos_los_niveles.pdf"
    )

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Genera el PDF completo.
        data = {"user": {"name": str, "position": str},
                "results": {"total_score": float, "nivel": str}}
        """
        nivel   = data["results"]["nivel"]
        score   = int(data["results"]["total_score"])
        name    = data["user"]["name"]
        position = data["user"]["position"]
        content = IE_CONTENT[nivel]

        # 1. Crear overlay con ReportLab
        overlay_buf = BytesIO()
        c = canvas.Canvas(overlay_buf, pagesize=(PAGE_W, PAGE_H))

        self._draw_nivel(c, nivel)
        self._draw_nombre_puesto(c, name, position)
        self._draw_frase(c, content["frase"])
        self._draw_score(c, score)
        self._draw_descripcion(c, content["descripcion"])
        self._draw_rec_header(c)
        self._draw_recomendaciones(c, content["recs"])
        self._draw_cierre(c)

        c.save()
        overlay_buf.seek(0)

        # 2. Merge overlay sobre template
        template_reader = pypdf.PdfReader(self.TEMPLATE_PATH)
        overlay_reader  = pypdf.PdfReader(overlay_buf)

        template_page = template_reader.pages[0]
        overlay_page  = overlay_reader.pages[0]
        template_page.merge_page(overlay_page)

        writer = pypdf.PdfWriter()
        writer.add_page(template_page)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    # ── helpers internos ──────────────────────────────────────────────────

    def _set_font(self, c: canvas.Canvas, name: str, size: float, color=C_WHITE):
        c.setFont(name, size)
        c.setFillColor(color)

    def _fit_text_width(self, text: str, font: str, size_start: int,
                        size_min: int, max_w: float) -> int:
        """Reduce font size hasta que el texto quepa en max_w. Retorna el size."""
        from reportlab.pdfbase.pdfmetrics import stringWidth
        size = size_start
        while size > size_min:
            if stringWidth(text, font, size) <= max_w:
                break
            size -= 1
        return size

    def _draw_nivel(self, c: canvas.Canvas, nivel: str):
        """Dibuja el texto del nivel dentro del badge hexagonal."""
        # Badge center fitz: (80, 362) → rl: (80, 730)
        cx = 80
        cy_rl = fitz_to_rl(362)
        size = self._fit_text_width(nivel, "Helvetica-Bold", 20, 12, 110)
        self._set_font(c, "Helvetica-Bold", size)
        c.drawCentredString(cx, cy_rl - size * 0.35, nivel)

    def _draw_nombre_puesto(self, c: canvas.Canvas, name: str, position: str):
        """Dibuja los valores de nombre y puesto junto a sus labels."""
        # NOMBRE: baseline fitz y=313 → rl=779, x=262
        size_n = self._fit_text_width(name.upper(), "Helvetica-Bold", 11, 7, 358)
        self._set_font(c, "Helvetica-Bold", size_n)
        c.drawString(262, fitz_to_rl(313), name.upper())

        # PUESTO: baseline fitz y=355 → rl=737, x=210
        size_p = self._fit_text_width(position, "Helvetica", 11, 7, 410)
        self._set_font(c, "Helvetica", size_p)
        c.drawString(210, fitz_to_rl(355), position)

    def _draw_frase(self, c: canvas.Canvas, frase: str):
        """Dibuja la frase del nivel en color teal."""
        # Zona: x0=148, y0=367, x1=580, y1=395 → w=432pt, h=28pt
        x0, zone_w = 148, 432
        y0_fitz, y1_fitz = 367, 395
        zone_h = y1_fitz - y0_fitz

        style = ParagraphStyle(
            "frase", fontName="Helvetica-Bold", fontSize=9,
            textColor=C_TEAL, leading=11, alignment=TA_LEFT,
        )
        # Ajustar font size para que quepa en la zona
        for fs in range(9, 5, -1):
            style.fontSize = fs
            style.leading  = fs * 1.3
            p = Paragraph(frase, style)
            _, ph = p.wrap(zone_w, 9999)
            if ph <= zone_h:
                break
        p.drawOn(c, x0, fitz_to_rl(y1_fitz))

    def _draw_score(self, c: canvas.Canvas, score: int):
        """Dibuja 'Tu puntuación fue: N puntos de un total de 40 puntos'."""
        text = f"Tu puntuaci\u00f3n fue:  {score} puntos de un total de 40 puntos"
        # zona: x=148, baseline fitz y=410 → rl=682
        size = self._fit_text_width(text, "Helvetica", 9, 6, 432)
        self._set_font(c, "Helvetica", size)
        c.drawString(148, fitz_to_rl(410), text)

    def _draw_descripcion(self, c: canvas.Canvas, desc: dict):
        """Dibuja el bloque de descripción: párrafos + bullets."""
        # Zona: (15, 418) → (615, 582) = 600pt wide, 164pt tall
        x0, y0_fitz, x1, y1_fitz = 15, 418, 615, 582
        zone_w = x1 - x0
        zone_h = y1_fitz - y0_fitz

        # Construir items
        items = []
        items.append({"type": "para", "text": desc["parrafo1"]})
        if desc.get("bullets_header"):
            items.append({"type": "para", "text": desc["bullets_header"]})
        for b in desc.get("bullets", []):
            items.append({"type": "bullet", "text": b})
        items.append({"type": "para", "text": desc["parrafo2"]})

        self._draw_block(c, items, x0, y0_fitz, zone_w, zone_h,
                         fs_start=8, fs_min=6, bullet_indent=18)

    def _draw_rec_header(self, c: canvas.Canvas):
        """Dibuja el encabezado de recomendaciones."""
        text = "Recomendaciones para potenciar tu desarrollo:"
        # baseline fitz y=577 → rl=515
        size = self._fit_text_width(text, "Helvetica-Bold", 10, 7, 435)
        self._set_font(c, "Helvetica-Bold", size)
        c.drawString(15, fitz_to_rl(577), text)

    def _draw_recomendaciones(self, c: canvas.Canvas, recs: list):
        """Dibuja los 3 bloques de recomendaciones."""
        zones = [
            (42, 598, 375, 660),   # Rec 1: x0,y0,x1,y1 fitz
            (42, 662, 375, 720),   # Rec 2
            (42, 728, 375, 815),   # Rec 3
        ]
        for rec, (x0, y0_fitz, x1, y1_fitz) in zip(recs, zones):
            zone_w = x1 - x0
            zone_h = y1_fitz - y0_fitz
            items = self._rec_to_items(rec)
            self._draw_block(c, items, x0, y0_fitz, zone_w, zone_h,
                             fs_start=8, fs_min=6, bullet_indent=14,
                             title_bold=True)

    def _rec_to_items(self, rec: dict) -> list:
        """Convierte un dict de recomendación a lista de items para _draw_block."""
        items = [{"type": "title", "text": rec["titulo"]}]
        if rec.get("subtitulo"):
            items.append({"type": "para", "text": rec["subtitulo"]})
        if rec.get("cuerpo"):
            items.append({"type": "para", "text": rec["cuerpo"]})
        for b in rec.get("bullets", []):
            items.append({"type": "bullet", "text": b})
        if rec.get("bold_final"):
            items.append({"type": "bold", "text": rec["bold_final"]})
        return items

    def _draw_cierre(self, c: canvas.Canvas):
        """Dibuja las 2 líneas de cierre centradas."""
        # Zona centrada: cx=315, fitz y=822-862
        lines = [
            ("Helvetica",      8, "Este resultado no te define; solo refleja c\u00f3mo gestionas hoy tus emociones."),
            ("Helvetica-Bold", 8, '\u201cLa inteligencia emocional no es un rasgo fijo, es una habilidad entrenable\u201d.'),
        ]
        # baseline de línea 1: fitz y=835 → rl=257
        # baseline de línea 2: fitz y=850 → rl=242
        baselines_fitz = [835, 851]
        cx = PAGE_W / 2

        for (font, size, text), y_fitz in zip(lines, baselines_fitz):
            fs = self._fit_text_width(text, font, size, 6, 540)
            self._set_font(c, font, fs)
            c.drawCentredString(cx, fitz_to_rl(y_fitz), text)

    # ── _draw_block: motor de renderizado de bloques de texto con autofit ──

    def _draw_block(
        self, c: canvas.Canvas,
        items: list,
        x0: float, y0_fitz: float,
        zone_w: float, zone_h: float,
        fs_start: int = 8, fs_min: int = 6,
        bullet_indent: float = 14,
        title_bold: bool = False,
    ):
        """
        Dibuja una lista de items dentro de una zona, reduciendo font si no cabe.

        items: lista de dicts con keys:
          type: 'title' | 'para' | 'bullet' | 'bold'
          text: str

        Coordenadas en fitz (top-left). Convierte internamente a RL.
        """
        for fs in range(fs_start, fs_min - 1, -1):
            leading     = round(fs * 1.35)
            title_size  = min(fs + 2, 11) if title_bold else fs
            title_lead  = round(title_size * 1.3)

            paragraphs = []
            for item in items:
                t = item["type"]
                txt = item["text"]

                if t == "title":
                    style = ParagraphStyle(
                        "t", fontName="Helvetica-Bold", fontSize=title_size,
                        textColor=C_WHITE, leading=title_lead,
                        spaceAfter=2, alignment=TA_LEFT,
                    )
                    paragraphs.append(Paragraph(txt, style))

                elif t == "para":
                    style = ParagraphStyle(
                        "p", fontName="Helvetica", fontSize=fs,
                        textColor=C_WHITE, leading=leading,
                        spaceAfter=2, alignment=TA_JUSTIFY,
                    )
                    paragraphs.append(Paragraph(txt, style))

                elif t == "bullet":
                    style = ParagraphStyle(
                        "b", fontName="Helvetica", fontSize=fs,
                        textColor=C_WHITE, leading=leading,
                        leftIndent=bullet_indent, firstLineIndent=0,
                        spaceAfter=1, alignment=TA_LEFT,
                    )
                    paragraphs.append(Paragraph(f"\u2022 {txt}", style))

                elif t == "bold":
                    style = ParagraphStyle(
                        "bf", fontName="Helvetica-Bold", fontSize=fs,
                        textColor=C_WHITE, leading=leading,
                        spaceAfter=1, alignment=TA_LEFT,
                    )
                    paragraphs.append(Paragraph(txt, style))

            # Medir altura total
            total_h = sum(p.wrap(zone_w, 9999)[1] for p in paragraphs)

            if total_h <= zone_h or fs == fs_min:
                # Dibujar desde y0_fitz hacia abajo
                y_rl = fitz_to_rl(y0_fitz)   # top de la zona en RL
                for p in paragraphs:
                    _, ph = p.wrap(zone_w, 9999)
                    y_rl -= ph
                    p.drawOn(c, x0, y_rl)
                return
