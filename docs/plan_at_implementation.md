# Plan de Implementación — Test Alfabetización Tecnológica (AT)

## Contexto del Proyecto

**Skillera** — plataforma de diagnósticos por WhatsApp con Kommo CRM y n8n. Actualmente 1 test operativo: **Inteligencia Emocional (IE)**. Este plan agrega el segundo: **Alfabetización Tecnológica (AT)**.

> **Liderazgo** existe en n8n pero está deshabilitado y pendiente de eliminación. NO usarlo como referencia.

### IDs y Referencias
| Recurso | ID / Valor |
|---------|------------|
| Chatbot AT | `2KhIR3MCBotra5qe` |
| AT Process Question | `8cv7GiAK6nIOLpXM` |
| Calculate AT Scores | `p0rkK6Ft0UWzzeFI` |
| AT Responses Data Table | `B4pPUen5ysuETffw` |
| Sessions Data Table | `tBaZMEOVw2tvcswf` |
| Send File via Kommo Chat | `uuAzYnZJtzpxVNd3` |
| Salesbot bot_id (AT) | `64784` |
| Kommo field tests_completados | `2283634` |

---

## Definición del Test AT

- **Código interno:** `at`
- **Datos personales:** solo nombre (NO email, NO puesto)
- **10 preguntas** con respuestas A/B/C. Scoring: A=1, B=2, C=3. Rango: 10–30 pts.
- **11 steps:** step 1=nombre, steps 2–11=Q1-Q10, step 12=processing
- **3 niveles:** Básico/Explorador (10-17), Intermedio/Adaptador (18-25), Avanzado/Líder Digital (26-30)

---

# PARTE 1 ✅ COMPLETADA

Flujo conversacional completo implementado y verificado en producción. Todos los workflows y Data Tables están activos.

**Flujo:** Agente escribe `at` en Kommo → Agent Commands crea sesión y envía bienvenida + pregunta nombre → cliente responde → Dispatcher enruta a Chatbot AT → 10 preguntas A/B/C → Calculate AT Scores → mensaje "Generando diagnóstico..." → **aquí termina Parte 1**.

---

# PARTE 2 — Generación PDF (EJECUTABLE)

## Qué hacer

Replicar el patrón IE completo: misma arquitectura de `IEPDFGenerator` pero para AT. Seguir `services/ie_pdf_generator.py` como referencia directa — misma técnica de pre-rasterización, overlay con `page.insert_text(fontfile=...)`, mismas fuentes Montserrat.

## Assets

Copiar a `assets/` y agregar excepciones en `.gitignore`:

| Archivo original | Renombrar a | Nivel |
|---|---|---|
| `1777000225794_Diagnostico_AT_Basico.pdf` | `Diagnostico_AT_Basico_Skillera.pdf` | Básico (10-17) |
| `1777000225794_Diagnostico_AT_Medio.pdf` | `Diagnostico_AT_Intermedio_Skillera.pdf` | Intermedio (18-25) |
| `1777000225794_Diagnostico_AT_Avanzado.pdf` | `Diagnostico_AT_Avanzado_Skillera.pdf` | Avanzado (26-30) |
| `skillnauta.png` | `skillnauta.png` | Ya embebida en los PDFs |

## Campos dinámicos — Solo 2

**Ninguna plantilla tiene campo "Puesto:".** Las 3 solo tienen "Nombre:".

| Campo | Ubicación en el PDF |
|---|---|
| **Nombre** | Derecha de "Nombre:" en "Informe Integrado de Resultados" |
| **Score** (entero 10-30) | Gap entre "Tu puntuación fue:" y "puntos de un total de 30 puntos" |

Medir coordenadas con `page.get_text("dict")` para cada template. Varían entre niveles.

## Archivos a crear

### 1. `models/at_schemas.py`
Seguir el patrón de `models/ie_schemas.py` con estas diferencias:
- `ATUserData`: solo campo `name` (NO `position`)
- `ATResults`: `total_score` (int, 10-30), `nivel` (Básico | Intermedio | Avanzado)
- `ATPDFRequest`, `ATPDFResponse`: misma estructura que IE

### 2. `services/at_pdf_generator.py`
Seguir el patrón de `services/ie_pdf_generator.py` con estas diferencias:
- 3 templates AT (no 3 IE)
- Solo 2 overlays: nombre + score (IE tiene 3: nombre, puesto, score)
- Usar nombres internos de fuente `"at_bold"` / `"at_light"` (distintos a IE para evitar conflicto)
- Medir y definir `_LAYOUT` con 4 coordenadas por nivel: `(nombre_x, nombre_y, score_cx, score_y)`

### 3. Endpoints en `main.py`
Seguir el patrón de los endpoints IE existentes:
- `POST /generate-at-pdf` → binary
- `POST /generate-at-pdf-base64` → base64
- Singleton `at_generator = ATPDFGenerator()` al nivel del IE
- Filename: `diagnostico_at_{name}_{date}.pdf`

### 4. Actualizar imports
- `models/__init__.py`
- `services/__init__.py`

## Deploy
Push → Render autodeploy → verificar `/health` → probar con 3 payloads (score 10, 22, 28)

## Nodos finales n8n (Post-PDF)

Agregar al workflow `AT Process Question` (`8cv7GiAK6nIOLpXM`) después del nodo `AT.PQ.10e Call Calculate AT Scores`:

### H.1 — HTTP Request: Generar PDF
POST a `{{ $vars.PDF_GENERATOR_URL }}/generate-at-pdf-base64` con timeout 60s y 2 retries.
Body: `{ "user": { "name": "..." }, "results": { "total_score": N, "nivel": "..." } }`

### H.2 — Enviar PDF por WhatsApp
Execute Workflow → `Send File via Kommo Chat` (`uuAzYnZJtzpxVNd3`)

### H.3 — Mensaje de completado
PATCH field[32] → Salesbot `64784` → Wait 2s → Clear.
Texto: `Tu diagnostico esta listo. Revisalo arriba.` (sin emojis SMP)

### H.4 — PATCH tests_completados
field_id `2283634` → activa silence gate en Dispatcher

### H.5 — Cleanup
DELETE en `sessions` y `at_responses` WHERE phone_number = contact_id

---

## Orden de ejecución

1. Copiar assets, actualizar `.gitignore`
2. Crear schemas (`at_schemas.py`)
3. Crear generador (`at_pdf_generator.py`) — medir coordenadas primero
4. Agregar endpoints + imports
5. Deploy y verificar
6. Agregar nodos H.1-H.5 en n8n
7. Testing end-to-end

---

## Lecciones aprendidas

1. **`page.insert_text(fontfile=...)`** renderiza sobre PDFs Canva. `TextWriter.write_text()` NO (texto invisible).
2. **Pre-rasterizar templates al startup** — elimina 46 MB pixmap/request.
3. **Score centrado:** `x = gap_center - (text_width / 2)`.
4. **`deflate=True, garbage=4`** en save. Si `clean=True` infla tamaño → usar `clean=False`.
5. **Fuentes con nombres internos únicos** (`"at_bold"` / `"at_light"`) para evitar conflicto con IE.
6. **Emojis SMP rompen mensajes Kommo.** Solo usar BMP (⚠️ ⚡ →).
7. **Patrón WhatsApp:** PATCH field[32] → Salesbot → Wait 2s → Clear.
8. **`entity_type` = string `"2"`** en salesbot, `continueOnFail: true` en PATCHs.
9. **`n8n_update_full_workflow`** obligatorio para cambios estructurales. Partial corrompe conexiones.
