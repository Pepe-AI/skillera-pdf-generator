"""
Recreate [Skillera] Chatbot AT without puesto step.
11 steps: step 1=nombre, steps 2-11=Q1-Q10, step 12=processing
"""
import json, urllib.request, ssl

N8N_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMDYyOGNmYi04MGYxLTQwMjUtYmE1MC02ZDJkZWZjNmY4ZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiN2MxMTM5ZTYtNzQ2OS00ZTAwLThkODMtZDRkODcyNjEwNzNhIiwiaWF0IjoxNzcyNjAyOTk5fQ.XbXiBQztJgmH07BPqlO1HCX2iGpm6klvVpQ378WozKM'
ctx = ssl.create_default_context()
CHATBOT_AT_ID = '2KhIR3MCBotra5qe'
AT_PROCESS_QUESTION_WF = '8cv7GiAK6nIOLpXM'
SESSIONS_TABLE = 'tBaZMEOVw2tvcswf'
AT_RESPONSES_TABLE = 'B4pPUen5ysuETffw'
BOT_ID = 64784

def sf(name, ftype="string"):
    return {"id": name, "displayName": name, "required": False, "defaultMatch": False,
            "display": True, "type": ftype, "readOnly": False, "removed": False}

def sf_exec(name, ftype="string"):
    return {"id": name, "displayName": name, "required": False, "defaultMatch": False,
            "display": True, "canBeUsedToMatch": True, "type": ftype, "removed": False}

nodes = []
connections = {}

def add(nid, name, ntype, ver, pos, params, **extra):
    node = {"id": nid, "name": name, "type": f"n8n-nodes-base.{ntype}",
            "typeVersion": ver, "position": pos, "parameters": params}
    node.update(extra)
    nodes.append(node)

def conn(src, dst, src_out=0):
    if src not in connections:
        connections[src] = {"main": []}
    main = connections[src]["main"]
    while len(main) <= src_out:
        main.append([])
    main[src_out].append({"node": dst, "type": "main", "index": 0})

# ── 1. Trigger ──
add("at-trigger", "Trigger from Dispatcher", "executeWorkflowTrigger", 1.1, [-3072, 304], {
    "inputSource": "jsonExample",
    "jsonExample": json.dumps({
        "message_text": "hola", "contact_id": "36013062", "entity_id": "34667542",
        "chat_id": "53d9b32a", "author_name": "Test", "lead_id": "34667542",
        "kommo_field_id": "2263666", "kommo_token": "TOKEN",
        "kommo_dominio": "https://sur20ciudaddemrxico.kommo.com"
    }, indent=2)
})

# ── 2. Check Session ──
add("at-check-session", "AT.1 Check Session", "dataTable", 1.1, [-2848, 304], {
    "operation": "get",
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $('Trigger from Dispatcher').item.json.contact_id }}"}]},
    "limit": 1
}, alwaysOutputData=True)

# ── 3. Handle Session ──
add("at-handle-session", "AT.2 Handle Session", "code", 2, [-2624, 304], {
    "jsCode": "const trigger = $('Trigger from Dispatcher').first().json;\nlet session = null;\ntry {\n  const items = $input.all();\n  if (items && items.length > 0 && items[0].json && items[0].json.id) {\n    session = items[0].json;\n  }\n} catch(e) {}\nconst currentStep = session ? (parseInt(session.current_step) || 0) : 0;\nreturn [{ json: { ...trigger, session_exists: !!session, session: session, current_step: currentStep } }];"
})

# ── 4. Session Exists? ──
add("at-session-exists", "AT.3 Session Exists?", "if", 2.2, [-2400, 304], {
    "conditions": {"options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "sess", "leftValue": "={{ $json.session_exists }}", "rightValue": True,
                        "operator": {"type": "boolean", "operation": "equals"}}], "combinator": "and"},
    "options": {}
})

# ── 5. Create New Session (step=1, NO puesto) ──
add("at-new-session", "AT.4 Create New Session", "dataTable", 1.1, [-2032, 560], {
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "columns": {"mappingMode": "defineBelow",
        "value": {"phone_number": "={{ $json.contact_id }}", "current_step": "=1",
                  "name": "", "email": "", "jobPosition": "",
                  "started_at": "={{ $now.toISO() }}", "last_interaction": "={{ $now.toISO() }}",
                  "status": "active", "test_type": "at"},
        "matchingColumns": [],
        "schema": [sf("phone_number"), sf("current_step", "number"), sf("name"), sf("email"),
                   sf("jobPosition"), sf("started_at"), sf("last_interaction"), sf("status"), sf("test_type")],
        "attemptToConvertTypes": False, "convertFieldsToString": False},
    "options": {}
})

# ── 6. Insert blank at_responses ──
qv = {"phone_number": "={{ $('Trigger from Dispatcher').item.json.contact_id }}"}
for i in range(1, 11): qv[f"q{i}"] = ""
qs = [sf("phone_number")] + [sf(f"q{i}") for i in range(1, 11)]
add("at-new-responses", "AT.4b Create AT Responses", "dataTable", 1.1, [-1808, 680], {
    "dataTableId": {"__rl": True, "value": AT_RESPONSES_TABLE, "mode": "id"},
    "columns": {"mappingMode": "defineBelow", "value": qv, "matchingColumns": [], "schema": qs,
                "attemptToConvertTypes": False, "convertFieldsToString": False},
    "options": {}
})

# ── 7. Build Welcome ──
# Welcome message + ask for name directly
welcome_js = (
    "const trigger = $('Trigger from Dispatcher').first().json;\n"
    "const msg1 = '\\ud83d\\ude80 *\\u00bfQu\\u00e9 tan listo est\\u00e1s para el trabajo del futuro?*\\n\\n"
    "\\u00a1Hola! \\ud83d\\udc4b Este test r\\u00e1pido te dir\\u00e1 si tienes las habilidades digitales que las empresas buscan hoy. "
    "No es un examen, es una br\\u00fajula para tu carrera.\\n\\n"
    "Vamos a medir 5 \\u00e1reas clave:\\n"
    "\\ud83c\\udf10 Fundamentos y Nube\\n"
    "\\ud83d\\udee1\\ufe0f Seguridad Digital\\n"
    "\\ud83e\\udd16 Inteligencia Artificial\\n"
    "\\u26a1 Agilidad y Trabajo en Equipo\\n"
    "\\ud83e\\udde0 \\u00c9tica y Futuro\\n\\n"
    "Primero necesito un dato. \\ud83d\\udcdd';\n"
    "const msg2 = '\\u00bfCu\\u00e1l es tu nombre completo?';\n"
    "const fieldId = parseInt(trigger.kommo_field_id);\n"
    "const patch1 = { custom_fields_values: [{ field_id: fieldId, values: [{ value: msg1 }] }] };\n"
    "const patch2 = { custom_fields_values: [{ field_id: fieldId, values: [{ value: msg2 }] }] };\n"
    "return [{ json: { ...trigger, current_step: 1, patch_body_string: JSON.stringify(patch1), "
    "patch_body_string_2: JSON.stringify(patch2) } }];"
)
add("at-send-welcome", "AT.5 Build Welcome", "code", 2, [-1584, 560], {"jsCode": welcome_js})

# WhatsApp sending pattern helper
def add_whatsapp_chain(prefix, pos_start, src_node, msg_field="patch_body_string"):
    """Add PATCH -> Salesbot -> Wait -> Clear chain."""
    px, py = pos_start
    patch_id = f"{prefix}-patch"
    sb_id = f"{prefix}-sb"
    wait_id = f"{prefix}-wait"
    clear_id = f"{prefix}-clear"

    add(patch_id, f"{prefix} PATCH", "httpRequest", 4.2, [px, py], {
        "method": "PATCH",
        "url": f"={{{{ $json.kommo_dominio }}}}/api/v4/leads/{{{{ $json.lead_id }}}}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": f"=Bearer {{{{ $json.kommo_token }}}}"},
            {"name": "content-type", "value": "application/json"},
            {"name": "accept", "value": "application/json"}
        ]},
        "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
        "body": f"={{{{ $json.{msg_field} }}}}", "options": {}
    }, continueOnFail=True)

    add(sb_id, f"{prefix} Salesbot", "httpRequest", 4.2, [px+208, py], {
        "method": "POST",
        "url": f"={{{{ $('{src_node}').item.json.kommo_dominio }}}}/api/v2/salesbot/run",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": f"=Bearer {{{{ $('{src_node}').item.json.kommo_token }}}}"},
            {"name": "accept", "value": "application/json"}
        ]},
        "sendBody": True, "specifyBody": "json",
        "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'{src_node}\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
        "options": {}
    }, continueOnFail=True)

    add(wait_id, f"Wait 2s {prefix}", "wait", 1.1, [px+416, py], {"amount": 2})

    add(clear_id, f"{prefix} Clear", "httpRequest", 4.2, [px+560, py], {
        "method": "PATCH",
        "url": f"={{{{ $('{src_node}').item.json.kommo_dominio }}}}/api/v4/leads/{{{{ $('{src_node}').item.json.lead_id }}}}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": f"=Bearer {{{{ $('{src_node}').item.json.kommo_token }}}}"},
            {"name": "content-type", "value": "application/json"}
        ]},
        "sendBody": True,
        "bodyParameters": {"parameters": [
            {"name": "custom_fields_values",
             "value": f"={{{{ [{{field_id: parseInt($('{src_node}').item.json.kommo_field_id), values: [{{value: ''}}]}}] }}}}"}
        ]}, "options": {}
    }, continueOnFail=True)

    # Return node names for chaining
    return f"{prefix} PATCH", f"{prefix} Salesbot", f"Wait 2s {prefix}", f"{prefix} Clear"

# Welcome chain 1
p1, s1, w1, c1 = add_whatsapp_chain("AT.5a", (-1376, 560), "AT.5 Build Welcome")
# Welcome chain 2 (nombre question)
# Need special PATCH for msg2
add("at-patch-w2", "AT.5d PATCH Welcome 2", "httpRequest", 4.2, [-544, 560], {
    "method": "PATCH",
    "url": "={{ $('AT.5 Build Welcome').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.5 Build Welcome').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.5 Build Welcome').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ $('AT.5 Build Welcome').item.json.patch_body_string_2 }}", "options": {}
}, continueOnFail=True)

add("at-sb-w2", "AT.5e Salesbot W2", "httpRequest", 4.2, [-336, 560], {
    "method": "POST",
    "url": "={{ $('AT.5 Build Welcome').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.5 Build Welcome').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'AT.5 Build Welcome\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

add("wait-at-w2", "Wait 2s W2", "wait", 1.1, [-128, 560], {"amount": 2})

add("at-clear-w2", "AT.5f Clear W2", "httpRequest", 4.2, [80, 560], {
    "method": "PATCH",
    "url": "={{ $('AT.5 Build Welcome').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.5 Build Welcome').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.5 Build Welcome').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]},
    "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values",
         "value": "={{ [{field_id: parseInt($('AT.5 Build Welcome').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# ── 8. Router por Step (2 outputs: step 1=name, step >= 2=questions) ──
add("at-router-step", "AT.6 Router por Step", "switch", 3.2, [-2176, 160], {
    "rules": {"values": [
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [{"id": "step1", "leftValue": "={{ $json.current_step }}", "rightValue": 1,
                           "operator": {"type": "number", "operation": "equals"}}], "combinator": "and"}},
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [{"id": "step2plus", "leftValue": "={{ $json.current_step }}", "rightValue": 1,
                           "operator": {"type": "number", "operation": "gt"}}], "combinator": "and"}}
    ]}, "options": {}
})

# ── 9. Call AT Process Question ──
pq_fields = ["message_text", "contact_id", "entity_id", "lead_id", "current_step", "kommo_field_id", "kommo_token", "kommo_dominio"]
pq_schema = [sf_exec(f, "number" if f == "current_step" else "string") for f in pq_fields]
pq_value = {f: f"={{{{ $json.{f} }}}}" for f in pq_fields}
pq_value["kommo_field_id"] = "={{ String($json.kommo_field_id) }}"

add("at-call-process-q", "AT.7 Call AT Process Question", "executeWorkflow", 1.2, [-1952, 320], {
    "workflowId": {"__rl": True, "value": AT_PROCESS_QUESTION_WF, "mode": "id"},
    "workflowInputs": {"mappingMode": "defineBelow", "value": pq_value, "matchingColumns": [],
                       "schema": pq_schema, "attemptToConvertTypes": False, "convertFieldsToString": True},
    "options": {}
})

# ── 10. Step 1: Validate Name ──
add("at-s1-validate", "S1 Validar Nombre", "code", 2, [-1680, -64], {
    "jsCode": "const text = ($json.message_text || '').trim();\nconst isValid = text.length >= 2;\nreturn [{ json: { ...$json, validation: { valid: isValid, value: isValid ? text : null,\n  error_message: isValid ? '' : '\\u26a0\\ufe0f Por favor escribe tu nombre completo (m\\u00ednimo 2 caracteres).' } } }];"
})

add("at-s1-valid-check", "S1.1 Nombre Valido?", "if", 2.2, [-1456, -64], {
    "conditions": {"options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "nv", "leftValue": "={{ $json.validation.valid }}", "rightValue": True,
                        "operator": {"type": "boolean", "operation": "equals"}}], "combinator": "and"},
    "options": {}
})

# Save Name -> set step=2 (next is first question)
add("at-s1-save", "S1.2 Guardar Nombre", "dataTable", 1.1, [-1232, -192], {
    "operation": "update",
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $json.contact_id }}"}]},
    "columns": {"mappingMode": "defineBelow",
        "value": {"name": "={{ $json.validation.value }}", "current_step": "=2", "last_interaction": "={{ $now.toISO() }}"},
        "matchingColumns": [],
        "schema": [sf("phone_number"), sf("name"), sf("current_step", "number"), sf("last_interaction")],
        "attemptToConvertTypes": False, "convertFieldsToString": False},
    "options": {}
})

# After name saved -> send transition + Q1 directly (no puesto step)
transition_js = (
    "const trigger = $('Trigger from Dispatcher').first().json;\n"
    "const q1Text = '\\u00a1Perfecto! \\ud83d\\ude80 Vamos a comenzar.\\n\\n"
    "Son 10 preguntas r\\u00e1pidas. Para cada una elige la opci\\u00f3n que m\\u00e1s se parezca a lo que t\\u00fa har\\u00edas en la vida real.\\n\\n"
    "Responde siempre con la letra de tu opci\\u00f3n: *A*, *B* o *C*\\n\\n"
    "\\u00a1Empecemos! \\ud83d\\udc47\\n\\n"
    "*Pregunta 1 de 10* \\ud83c\\udf10\\n\\n"
    "Si te piden trabajar en un archivo con un compa\\u00f1ero al mismo tiempo, t\\u00fa:\\n\\n"
    "A) Me confundo. Prefiero hacerlo yo solo y mandarlo luego por correo.\\n"
    "B) S\\u00e9 que se puede por internet, pero me da miedo que alguien borre mi parte.\\n"
    "C) \\u00a1Me encanta! Uso herramientas en la \"Nube\" para que avancemos juntos en vivo.\\n\\n"
    "\\u2192 Responde con la letra: *A*, *B* o *C*';\n"
    "const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: q1Text }] }] };\n"
    "return [{ json: { ...trigger, patch_body_string: JSON.stringify(patchBody) } }];"
)
add("at-s1-transition", "S1.3 Build Transicion + Q1", "code", 2, [-1008, -192], {"jsCode": transition_js})

p_t, s_t, w_t, c_t = add_whatsapp_chain("S1.4", (-784, -192), "S1.3 Build Transicion + Q1")

# Error Name
add("at-s1-error", "S1.E Build Error Nombre", "code", 2, [-1248, -16], {
    "jsCode": "const trigger = $('Trigger from Dispatcher').first().json;\nconst errMsg = $('S1 Validar Nombre').first().json.validation.error_message;\nconst msgText = errMsg + '\\n\\n\\u00bfCu\\u00e1l es tu nombre completo?';\nconst patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: msgText }] }] };\nreturn [{ json: { ...trigger, patch_body_string: JSON.stringify(patchBody) } }];"
})

p_e, s_e, w_e, c_e = add_whatsapp_chain("S1.E1", (-1008, -16), "S1.E Build Error Nombre")

# ── Connections ──
conn("Trigger from Dispatcher", "AT.1 Check Session")
conn("AT.1 Check Session", "AT.2 Handle Session")
conn("AT.2 Handle Session", "AT.3 Session Exists?")
conn("AT.3 Session Exists?", "AT.6 Router por Step", 0)   # TRUE
conn("AT.3 Session Exists?", "AT.4 Create New Session", 1) # FALSE

# New session
conn("AT.4 Create New Session", "AT.4b Create AT Responses")
conn("AT.4b Create AT Responses", "AT.5 Build Welcome")
conn("AT.5 Build Welcome", p1)
conn(p1, s1); conn(s1, w1); conn(w1, c1)
conn(c1, "AT.5d PATCH Welcome 2")
conn("AT.5d PATCH Welcome 2", "AT.5e Salesbot W2")
conn("AT.5e Salesbot W2", "Wait 2s W2")
conn("Wait 2s W2", "AT.5f Clear W2")

# Router
conn("AT.6 Router por Step", "S1 Validar Nombre", 0)          # step 1
conn("AT.6 Router por Step", "AT.7 Call AT Process Question", 1) # step >= 2

# Step 1: Name
conn("S1 Validar Nombre", "S1.1 Nombre Valido?")
conn("S1.1 Nombre Valido?", "S1.2 Guardar Nombre", 0)   # TRUE
conn("S1.1 Nombre Valido?", "S1.E Build Error Nombre", 1) # FALSE
conn("S1.2 Guardar Nombre", "S1.3 Build Transicion + Q1")
conn("S1.3 Build Transicion + Q1", p_t)
conn(p_t, s_t); conn(s_t, w_t); conn(w_t, c_t)
conn("S1.E Build Error Nombre", p_e)
conn(p_e, s_e); conn(s_e, w_e); conn(w_e, c_e)

# ── Build workflow ──
workflow = {
    "name": "[Skillera] Chatbot AT",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner"}
}

# First deactivate old workflow
print("Deactivating old Chatbot AT...")
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{CHATBOT_AT_ID}/deactivate'
req = urllib.request.Request(url, method='POST', data=b'')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
req.add_header('Content-Type', 'application/json')
try:
    urllib.request.urlopen(req, context=ctx, timeout=30)
    print("  Deactivated OK")
except Exception as e:
    print(f"  Deactivate error: {e}")

# Update with full workflow
print("Updating Chatbot AT...")
allowed_settings = {'executionOrder', 'callerPolicy'}
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{CHATBOT_AT_ID}'
data = json.dumps(workflow).encode('utf-8')
req = urllib.request.Request(url, data=data, method='PUT')
req.add_header('Content-Type', 'application/json')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
try:
    resp = urllib.request.urlopen(req, context=ctx, timeout=60)
    result = json.loads(resp.read().decode())
    print(f"  Updated! Nodes: {len(result.get('nodes', []))}, version: {result.get('versionId')}")
except urllib.error.HTTPError as e:
    print(f"  ERROR {e.code}: {e.read().decode()[:500]}")

# Reactivate
print("Activating Chatbot AT...")
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{CHATBOT_AT_ID}/activate'
req = urllib.request.Request(url, method='POST', data=b'')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
req.add_header('Content-Type', 'application/json')
try:
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    result = json.loads(resp.read().decode())
    print(f"  Active: {result.get('active')}")
except Exception as e:
    print(f"  Activate error: {e}")

print("\nDone!")
