# Skillera PDF Generator

Generador de diagnósticos de habilidades de liderazgo automatizado.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
uvicorn main:app --reload --port 8000
```

## Estructura del Proyecto

```
├── README.md
├── .gitignore
├── requirements.txt
├── main.py
├── config.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── services/
│   ├── __init__.py
│   ├── pdf_generator.py
│   └── chart_generator.py
├── tests/
│   ├── __init__.py
│   └── test_endpoints.py
└── assets/
    ├── brand_colors.json
    └── skillera_logo.png
```

## Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Info del servicio |
| `/health` | GET | Verificación de salud |
| `/generate-pdf` | POST | Genera PDF (retorna archivo binario) |
| `/generate-pdf-base64` | POST | Genera PDF (retorna base64 para WhatsApp/Email) |
