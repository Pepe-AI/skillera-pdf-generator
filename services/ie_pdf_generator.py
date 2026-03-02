"""
IE PDF Generator — Diagnóstico de Inteligencia Emocional
Estrategia: ReportLab overlay (contenido dinámico) + pypdf merge sobre template vectorial.
Template: assets/template_ie.pdf  (1440 x 2557.5 pt, PDF vectorial)
"""

import os
from io import BytesIO

import pypdf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph
from reportlab.pdfbase.pdfmetrics import stringWidth

# ── Página ───────────────────────────────────────────────────────────────────
PAGE_W = 1440.0
PAGE_H = 2557.5


def _rl(fitz_y: float) -> float:
    """Convierte Y de sistema fitz (top-left) a ReportLab (bottom-left)."""
    return PAGE_H - fitz_y


# ── Colores ──────────────────────────────────────────────────────────────────
C_WHITE = HexColor("#FFFFFF")
C_TEAL  = HexColor("#3CCBB2")

# ── Contenido por nivel ──────────────────────────────────────────────────────
IE_CONTENT = {
    "Bajo": {
        "frase": '"Tus emociones suelen gestionarse de forma reactiva o evitativa".',
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
                "bullets": ["\u00bfQu\u00e9 sent\u00ed hoy?", "\u00bfEn qu\u00e9 momento fue m\u00e1s intenso?", "\u00bfC\u00f3mo reaccion\u00e9?"],
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
        "frase": '"Reconoces lo que sientes, pero bajo presi\u00f3n vuelves a patrones autom\u00e1ticos".',
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
                "Este nivel es una base s\u00f3lida. La diferencia entre nivel medio y alto suele "
                "estar en la consistencia, especialmente en momentos de tensi\u00f3n."
            ),
        },
        "recs": [
            {
                "titulo": "Practica la regulaci\u00f3n antes de conversar",
                "subtitulo": "Antes de una conversaci\u00f3n dif\u00edcil, preg\u00fantate:",
                "bullets": ["\u00bfQu\u00e9 quiero lograr?", "\u00bfDesde qu\u00e9 emoci\u00f3n estoy hablando?"],
                "bold_final": "Esto aumenta la intenci\u00f3n consciente.",
            },
            {
                "titulo": "Pide feedback sobre tu impacto emocional",
                "subtitulo": "Pregunta a alguien de confianza:",
                "bullets": ['"Cuando estoy bajo presi\u00f3n, \u00bfc\u00f3mo me percibes?"'],
                "bold_final": "La autoconciencia se fortalece con retroalimentaci\u00f3n externa.",
            },
            {
                "titulo": "Desarrolla vocabulario emocional m\u00e1s amplio",
                "cuerpo": (
                    'No es solo "molesto" o "bien", practica diferenciar: frustrado, '
                    "decepcionado, ansioso, inseguro, exigente, etc."
                ),
                "bold_final": "Mayor precisi\u00f3n = mejor regulaci\u00f3n.",
            },
        ],
    },
    "Alto": {
        "frase": '"Gestionas tus emociones con conciencia y eliges c\u00f3mo responder".',
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


class IEPDFGenerator:
    """Genera PDFs del Diagnóstico IE con overlay sobre template vectorial."""

    TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "template_ie.pdf",
    )

    def generate_pdf(self, data: dict) -> BytesIO:
        """
        Genera el PDF completo.
        data = {
            "user":    {"name": str, "position": str},
            "results": {"total_score": float, "nivel": str}  # nivel: Bajo|Medio|Alto
        }
        """
        nivel    = data["results"]["nivel"]
        score    = int(data["results"]["total_score"])
        name     = data["user"]["name"]
        position = data["user"]["position"]
        content  = IE_CONTENT[nivel]

        # 1. Crear overlay transparente con ReportLab
        overlay_buf = BytesIO()
        c = canvas.Canvas(overlay_buf, pagesize=(PAGE_W, PAGE_H))

        self._draw_nombre(c, name)
        self._draw_puesto(c, position)
        self._draw_score(c, score)
        self._draw_nivel_badge(c, nivel)
        self._draw_frase(c, content["frase"])
        self._draw_descripcion(c, content["descripcion"])
        self._draw_rec_header(c)
        self._draw_recomendaciones(c, content["recs"])
        self._draw_cierre(c)

        c.save()
        overlay_buf.seek(0)

        # 2. Merge overlay sobre el template
        template_reader = pypdf.PdfReader(self.TEMPLATE_PATH)
        overlay_reader  = pypdf.PdfReader(overlay_buf)

        page = template_reader.pages[0]
        page.merge_page(overlay_reader.pages[0])

        writer = pypdf.PdfWriter()
        writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    # ── helpers privados ─────────────────────────────────────────────────────

    def _autofit_size(self, text: str, font: str, size_start: int,
                      size_min: int, max_w: float) -> int:
        """Reduce font size hasta que el texto quepa en max_w."""
        size = size_start
        while size > size_min and stringWidth(text, font, size) > max_w:
            size -= 1
        return size

    def _draw_nombre(self, c: canvas.Canvas, name: str):
        """Valor del nombre a la derecha del label 'Nombre:' del template."""
        # Label 'Nombre:' termina en x=193, baseline rl=1654
        max_w = 1390 - 201
        size  = self._autofit_size(name.upper(), "Helvetica-Bold", 33, 20, max_w)
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(C_WHITE)
        c.drawString(201, 1654, name.upper())

    def _draw_puesto(self, c: canvas.Canvas, position: str):
        """Valor del puesto a la derecha del label 'Puesto:' del template."""
        # Label 'Puesto:' termina en x=171, baseline rl=1609
        max_w = 1390 - 179
        size  = self._autofit_size(position, "Helvetica", 33, 20, max_w)
        c.setFont("Helvetica", size)
        c.setFillColor(C_WHITE)
        c.drawString(179, 1609, position)

    def _draw_score(self, c: canvas.Canvas, score: int):
        """Reemplaza el placeholder 'X puntos de 40 puntos' con el score real."""
        # Tapar el placeholder con un rect del color de fondo
        # Placeholder en y0=975, y1=1015 fitz → rl: 1543 a 1583
        c.setFillColor(HexColor("#0D0D1A"))
        c.rect(350, _rl(1020), 1050, 55, fill=1, stroke=0)

        # Dibujar el texto real
        text = f"Tu puntuaci\u00f3n fue:   {score} puntos de un total de 40 puntos"
        max_w = 1390 - 350
        size  = self._autofit_size(text, "Helvetica", 28, 18, max_w)
        c.setFont("Helvetica", size)
        c.setFillColor(C_WHITE)
        # Centrado horizontalmente igual que el placeholder original (center_x=792)
        text_w = stringWidth(text, "Helvetica", size)
        x = 792 - text_w / 2
        c.drawString(x, _rl(1010), text)

    def _draw_nivel_badge(self, c: canvas.Canvas, nivel: str):
        """Escribe el nivel centrado dentro del badge hexagonal vacío."""
        # Badge fitz: (74,1048)→(350,1450), center fitz=(212,1249), center rl=(212,1308)
        cx_rl = 212
        cy_rl = _rl(1249)
        size  = self._autofit_size(nivel, "Helvetica-Bold", 60, 36, 240)
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(C_WHITE)
        c.drawCentredString(cx_rl, cy_rl - size * 0.35, nivel)

    def _draw_frase(self, c: canvas.Canvas, frase: str):
        """Frase del nivel en color teal, zona: fitz (350,960)→(1390,1010)."""
        x0      = 350
        zone_w  = 1390 - 350   # 1040 pt
        zone_h  = 1010 - 960   # 50 pt

        for fs in range(28, 14, -1):
            style = ParagraphStyle(
                "fr", fontName="Helvetica-BoldOblique", fontSize=fs,
                textColor=C_TEAL, leading=int(fs * 1.3), alignment=TA_LEFT,
            )
            p = Paragraph(frase, style)
            _, ph = p.wrap(zone_w, 9999)
            if ph <= zone_h or fs == 15:
                p.drawOn(c, x0, _rl(960) - ph)
                break

    def _draw_descripcion(self, c: canvas.Canvas, desc: dict):
        """
        Bloque de descripción.
        Zona fitz: (42,1080)→(1402,1440)  — 1360pt wide, 360pt tall
        El badge ocupa x=74-350 en y=1048-1450, texto a la derecha en x=370.
        """
        x0     = 370
        zone_w = 1402 - 370    # 1032 pt
        zone_h = 1440 - 1080   # 360 pt

        items = self._desc_to_items(desc)
        self._draw_block(c, items, x0=x0, y0_fitz=1080,
                         zone_w=zone_w, zone_h=zone_h,
                         fs_start=22, fs_min=16)

    def _draw_rec_header(self, c: canvas.Canvas):
        """Header de recomendaciones: fitz y=1455-1510."""
        text = "Recomendaciones para potenciar tu desarrollo:"
        max_w = 760 - 42
        size  = self._autofit_size(text, "Helvetica-Bold", 26, 18, max_w)
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(C_WHITE)
        c.drawString(42, _rl(1455 + size * 0.8), text)

    def _draw_recomendaciones(self, c: canvas.Canvas, recs: list):
        """Dibuja el texto de las 3 recomendaciones junto a sus círculos."""
        zones = [
            (130, 1433, 760, 1648),   # Rec 1
            (130, 1658, 760, 1819),   # Rec 2
            (130, 1829, 760, 2075),   # Rec 3
        ]
        for rec, (x0, y0, x1, y1) in zip(recs, zones):
            items  = self._rec_to_items(rec)
            zone_w = x1 - x0
            zone_h = y1 - y0
            self._draw_block(c, items, x0=x0, y0_fitz=y0,
                             zone_w=zone_w, zone_h=zone_h,
                             fs_start=22, fs_min=16, title_bold=True)

    def _draw_cierre(self, c: canvas.Canvas):
        """2 líneas de cierre centradas. Zona fitz: y=2075-2130."""
        lines = [
            ("Helvetica",             20, "Este resultado no te define; solo refleja c\u00f3mo gestionas hoy tus emociones."),
            ("Helvetica-BoldOblique", 20, '"La inteligencia emocional no es un rasgo fijo, es una habilidad entrenable".'),
        ]
        cx = PAGE_W / 2
        baselines_fitz = [2095, 2118]

        for (font, size_start, text), y_fitz in zip(lines, baselines_fitz):
            size = self._autofit_size(text, font, size_start, 14, 1360)
            c.setFont(font, size)
            c.setFillColor(C_WHITE)
            c.drawCentredString(cx, _rl(y_fitz), text)

    # ── conversores de datos a items ────────────────────────────────────────

    def _desc_to_items(self, desc: dict) -> list:
        items = [{"type": "para", "text": desc["parrafo1"]}]
        if desc.get("bullets_header"):
            items.append({"type": "para", "text": desc["bullets_header"]})
        for b in desc.get("bullets", []):
            items.append({"type": "bullet", "text": b})
        items.append({"type": "para", "text": desc["parrafo2"]})
        return items

    def _rec_to_items(self, rec: dict) -> list:
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

    # ── motor de renderizado de bloques con autofit ─────────────────────────

    def _draw_block(
        self,
        c: canvas.Canvas,
        items: list,
        x0: float,
        y0_fitz: float,
        zone_w: float,
        zone_h: float,
        fs_start: int = 22,
        fs_min:   int = 16,
        bullet_indent: float = 28,
        title_bold: bool = False,
    ):
        """
        Dibuja una lista de items en una zona dada, reduciendo font size si no cabe.

        items: lista de dicts {type: 'title'|'para'|'bullet'|'bold', text: str}
        Coordenadas en fitz (y0_fitz = top de la zona). Convierte a RL internamente.
        """
        for fs in range(fs_start, fs_min - 1, -1):
            leading    = round(fs * 1.35)
            title_size = min(fs + 3, 28) if title_bold else fs
            title_lead = round(title_size * 1.3)
            space_after = max(2, fs // 5)

            paragraphs = []
            for item in items:
                t   = item["type"]
                txt = item["text"]

                if t == "title":
                    style = ParagraphStyle(
                        "tt", fontName="Helvetica-Bold", fontSize=title_size,
                        textColor=C_WHITE, leading=title_lead,
                        spaceAfter=space_after, alignment=TA_LEFT,
                    )
                    paragraphs.append(Paragraph(txt, style))

                elif t == "para":
                    style = ParagraphStyle(
                        "pp", fontName="Helvetica", fontSize=fs,
                        textColor=C_WHITE, leading=leading,
                        spaceAfter=space_after, alignment=TA_JUSTIFY,
                    )
                    paragraphs.append(Paragraph(txt, style))

                elif t == "bullet":
                    style = ParagraphStyle(
                        "bb", fontName="Helvetica", fontSize=fs,
                        textColor=C_WHITE, leading=leading,
                        leftIndent=bullet_indent, spaceAfter=space_after,
                        alignment=TA_LEFT,
                    )
                    paragraphs.append(Paragraph(f"\u2022 {txt}", style))

                elif t == "bold":
                    style = ParagraphStyle(
                        "bld", fontName="Helvetica-Bold", fontSize=fs,
                        textColor=C_WHITE, leading=leading,
                        spaceAfter=space_after, alignment=TA_LEFT,
                    )
                    paragraphs.append(Paragraph(txt, style))

            # Medir altura total
            total_h = sum(p.wrap(zone_w, 9999)[1] for p in paragraphs)

            if total_h <= zone_h or fs == fs_min:
                # Renderizar desde el top de la zona hacia abajo
                y_rl = _rl(y0_fitz)
                for p in paragraphs:
                    _, ph = p.wrap(zone_w, 9999)
                    y_rl -= ph
                    p.drawOn(c, x0, y_rl)
                return
