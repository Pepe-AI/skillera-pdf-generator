"""
Generate the [Skillera] Chatbot AT workflow JSON for n8n.
Replicates the Chatbot IE pattern adapted for AT test.
"""
import json

# ── Constants ──
AT_RESPONSES_TABLE = "B4pPUen5ysuETffw"
SESSIONS_TABLE = "tBaZMEOVw2tvcswf"
AT_PROCESS_QUESTION_WF = "8cv7GiAK6nIOLpXM"
BOT_ID = 64784

def schema_field(name, ftype="string"):
    return {"id": name, "displayName": name, "required": False, "defaultMatch": False,
            "display": True, "type": ftype, "readOnly": False, "removed": False}

def schema_field_exec(name, ftype="string"):
    return {"id": name, "displayName": name, "required": False, "defaultMatch": False,
            "display": True, "canBeUsedToMatch": True, "type": ftype, "removed": False}

nodes = []
connections = {}

def add_node(nid, name, ntype, ver, pos, params, **extra):
    node = {"id": nid, "name": name, "type": f"n8n-nodes-base.{ntype}",
            "typeVersion": ver, "position": pos, "parameters": params}
    node.update(extra)
    nodes.append(node)

def connect(src, dst, src_out=0, dst_in=0):
    if src not in connections:
        connections[src] = {"main": []}
    main = connections[src]["main"]
    while len(main) <= src_out:
        main.append([])
    main[src_out].append({"node": dst, "type": "main", "index": dst_in})

# ── 1. Trigger ──
add_node("at-trigger", "Trigger from Dispatcher", "executeWorkflowTrigger", 1.1, [-3072, 304], {
    "inputSource": "jsonExample",
    "jsonExample": json.dumps({
        "message_text": "hola", "contact_id": "36013062", "entity_id": "34667542",
        "chat_id": "53d9b32a-0000", "author_name": "Test User", "lead_id": "34667542",
        "kommo_field_id": "2263666", "kommo_token": "TOKEN",
        "kommo_dominio": "https://sur20ciudaddemrxico.kommo.com"
    }, indent=2)
})

# ── 2. Check Session ──
add_node("at-check-session", "AT.1 Check Session", "dataTable", 1.1, [-2848, 304], {
    "operation": "get",
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $('Trigger from Dispatcher').item.json.contact_id }}"}]},
    "limit": 1
}, alwaysOutputData=True)

# ── 3. Handle Session ──
handle_js = """const trigger = $('Trigger from Dispatcher').first().json;
let session = null;
try {
  const items = $input.all();
  if (items && items.length > 0 && items[0].json && items[0].json.id) {
    session = items[0].json;
  }
} catch(e) {}
const currentStep = session ? (parseInt(session.current_step) || 0) : 0;
return [{ json: { ...trigger, session_exists: !!session, session: session, current_step: currentStep } }];"""
add_node("at-handle-session", "AT.2 Handle Session", "code", 2, [-2624, 304], {"jsCode": handle_js})

# ── 4. Session Exists? IF ──
add_node("at-session-exists", "AT.3 Session Exists?", "if", 2.2, [-2400, 304], {
    "conditions": {
        "options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "sess-check", "leftValue": "={{ $json.session_exists }}",
                        "rightValue": True, "operator": {"type": "boolean", "operation": "equals"}}],
        "combinator": "and"
    }, "options": {}
})

# ── 5. Create New Session (DataTable) ──
session_schema = [schema_field(f) for f in ["phone_number", "name", "email", "jobPosition", "started_at", "last_interaction", "status", "test_type"]]
session_schema.insert(1, schema_field("current_step", "number"))

add_node("at-new-session", "AT.4 Create New Session", "dataTable", 1.1, [-2032, 560], {
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "columns": {
        "mappingMode": "defineBelow",
        "value": {
            "phone_number": "={{ $json.contact_id }}", "current_step": "=1",
            "name": "", "email": "", "jobPosition": "",
            "started_at": "={{ $now.toISO() }}", "last_interaction": "={{ $now.toISO() }}",
            "status": "active", "test_type": "at"
        },
        "matchingColumns": [], "schema": session_schema,
        "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# ── 6. Insert blank at_responses ──
q_schema = [schema_field("phone_number")] + [schema_field(f"q{i}") for i in range(1, 11)]
q_value = {"phone_number": "={{ $('Trigger from Dispatcher').item.json.contact_id }}"}
for i in range(1, 11):
    q_value[f"q{i}"] = ""

add_node("at-new-responses", "AT.4b Create AT Responses", "dataTable", 1.1, [-1808, 680], {
    "dataTableId": {"__rl": True, "value": AT_RESPONSES_TABLE, "mode": "id"},
    "columns": {
        "mappingMode": "defineBelow", "value": q_value, "matchingColumns": [],
        "schema": q_schema, "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# ── 7. Build Welcome ──
welcome_js = r"""const trigger = $('Trigger from Dispatcher').first().json;
const msg1 = '\ud83d\ude80 *\u00bfQu\u00e9 tan listo est\u00e1s para el trabajo del futuro?*\n\n\u00a1Hola! \ud83d\udc4b Este test r\u00e1pido te dir\u00e1 si tienes las habilidades digitales que las empresas buscan hoy. No es un examen, es una br\u00fajula para tu carrera.\n\nVamos a medir 5 \u00e1reas clave:\n\ud83c\udf10 Fundamentos y Nube\n\ud83d\udee1\ufe0f Seguridad Digital\n\ud83e\udd16 Inteligencia Artificial\n\u26a1 Agilidad y Trabajo en Equipo\n\ud83e\udde0 \u00c9tica y Futuro\n\nPrimero necesito unos datos. \ud83d\udcdd';
const msg2 = '\u00bfCu\u00e1l es tu nombre completo?';
const fieldId = parseInt(trigger.kommo_field_id);
const patch1 = { custom_fields_values: [{ field_id: fieldId, values: [{ value: msg1 }] }] };
const patch2 = { custom_fields_values: [{ field_id: fieldId, values: [{ value: msg2 }] }] };
return [{ json: { ...trigger, current_step: 1, patch_body_string: JSON.stringify(patch1), patch_body_string_2: JSON.stringify(patch2) } }];"""
add_node("at-send-welcome", "AT.5 Build Welcome", "code", 2, [-1584, 560], {"jsCode": welcome_js})

# ── 8-14. Welcome sending chain (2 messages) ──
# PATCH Welcome 1
add_node("at-patch-welcome", "AT.5a PATCH Welcome", "httpRequest", 4.2, [-1376, 560], {
    "method": "PATCH",
    "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ $json.patch_body_string }}", "options": {}
}, continueOnFail=True)

# Salesbot Welcome 1
add_node("at-salesbot-w1", "AT.5b Salesbot Welcome 1", "httpRequest", 4.2, [-1168, 560], {
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

add_node("wait-at-w1", "Wait 2s W1", "wait", 1.1, [-960, 560], {"amount": 2})

# Clear Welcome 1
add_node("at-clear-w1", "AT.5c Clear Welcome 1", "httpRequest", 4.2, [-752, 560], {
    "method": "PATCH",
    "url": "={{ $('AT.5 Build Welcome').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.5 Build Welcome').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.5 Build Welcome').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]},
    "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('AT.5 Build Welcome').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# PATCH Welcome 2 (nombre question)
add_node("at-patch-w2", "AT.5d PATCH Welcome 2", "httpRequest", 4.2, [-544, 560], {
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

add_node("at-salesbot-w2", "AT.5e Salesbot Welcome 2", "httpRequest", 4.2, [-336, 560], {
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

add_node("wait-at-w2", "Wait 2s W2", "wait", 1.1, [-128, 560], {"amount": 2})

add_node("at-clear-w2", "AT.5f Clear Welcome 2", "httpRequest", 4.2, [80, 560], {
    "method": "PATCH",
    "url": "={{ $('AT.5 Build Welcome').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.5 Build Welcome').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.5 Build Welcome').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]},
    "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('AT.5 Build Welcome').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# ── 15. Router por Step (Switch) ──
# Step 1 = name, Step 2 = puesto, Step >= 3 = questions
add_node("at-router-step", "AT.6 Router por Step", "switch", 3.2, [-2176, 160], {
    "rules": {"values": [
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [{"id": "step1", "leftValue": "={{ $json.current_step }}", "rightValue": 1,
                           "operator": {"type": "number", "operation": "equals"}}], "combinator": "and"}},
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [{"id": "step2", "leftValue": "={{ $json.current_step }}", "rightValue": 2,
                           "operator": {"type": "number", "operation": "equals"}}], "combinator": "and"}},
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [{"id": "step3plus", "leftValue": "={{ $json.current_step }}", "rightValue": 2,
                           "operator": {"type": "number", "operation": "gt"}}], "combinator": "and"}}
    ]}, "options": {}
})

# ── 16. Call AT Process Question ──
pq_fields = ["message_text", "contact_id", "entity_id", "lead_id", "current_step", "kommo_field_id", "kommo_token", "kommo_dominio"]
pq_schema = [schema_field_exec(f, "number" if f == "current_step" else "string") for f in pq_fields]
pq_value = {f: f"={{{{ $json.{f} }}}}" for f in pq_fields}
pq_value["kommo_field_id"] = "={{ String($json.kommo_field_id) }}"

add_node("at-call-process-q", "AT.7 Call AT Process Question", "executeWorkflow", 1.2, [-1952, 320], {
    "workflowId": {"__rl": True, "value": AT_PROCESS_QUESTION_WF, "mode": "id"},
    "workflowInputs": {
        "mappingMode": "defineBelow", "value": pq_value, "matchingColumns": [],
        "schema": pq_schema, "attemptToConvertTypes": False, "convertFieldsToString": True
    }, "options": {}
})

# ── 17-24. Step 1: Validate Name ──
validate_name_js = """const text = ($json.message_text || '').trim();
const isValid = text.length >= 2;
return [{ json: { ...$json, validation: { valid: isValid, value: isValid ? text : null,
  error_message: isValid ? '' : '\u26a0\ufe0f Por favor escribe tu nombre completo (m\u00ednimo 2 caracteres).' } } }];"""
add_node("at-s1-validate", "S1 Validar Nombre", "code", 2, [-1680, -64], {"jsCode": validate_name_js})

add_node("at-s1-valid-check", "S1.1 Nombre V\u00e1lido?", "if", 2.2, [-1456, -64], {
    "conditions": {"options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "name-valid", "leftValue": "={{ $json.validation.valid }}",
                        "rightValue": True, "operator": {"type": "boolean", "operation": "equals"}}],
        "combinator": "and"}, "options": {}
})

# Save Name
add_node("at-s1-save", "S1.2 Guardar Nombre", "dataTable", 1.1, [-1232, -192], {
    "operation": "update",
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $json.contact_id }}"}]},
    "columns": {
        "mappingMode": "defineBelow",
        "value": {"name": "={{ $json.validation.value }}", "current_step": "=2", "last_interaction": "={{ $now.toISO() }}"},
        "matchingColumns": [], "schema": [schema_field("phone_number"), schema_field("name"), schema_field("current_step", "number"), schema_field("last_interaction")],
        "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# Ask Puesto
ask_puesto_js = r"""const trigger = $('Trigger from Dispatcher').first().json;
const msgText = '\u00bfCu\u00e1l es tu puesto actual?';
const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: msgText }] }] };
return [{ json: { ...trigger, patch_body_string: JSON.stringify(patchBody) } }];"""
add_node("at-s1-ask-puesto", "S1.3 Preguntar Puesto", "code", 2, [-1008, -192], {"jsCode": ask_puesto_js})

add_node("at-s1-patch", "S1.4 PATCH Pregunta Puesto", "httpRequest", 4.2, [-784, -192], {
    "method": "PATCH", "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}, {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ $json.patch_body_string }}", "options": {}
}, continueOnFail=True)

add_node("at-s1-salesbot", "S1.5 Salesbot Puesto", "httpRequest", 4.2, [-560, -192], {
    "method": "POST", "url": "={{ $('S1.3 Preguntar Puesto').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S1.3 Preguntar Puesto').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'S1.3 Preguntar Puesto\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

add_node("wait-at-s1", "Wait 2s S1", "wait", 1.1, [-448, -192], {"amount": 2})

add_node("at-s1-clear", "S1.6 Clear Salesbot Puesto", "httpRequest", 4.2, [-336, -192], {
    "method": "PATCH", "url": "={{ $('S1.3 Preguntar Puesto').item.json.kommo_dominio }}/api/v4/leads/{{ $('S1.3 Preguntar Puesto').item.json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S1.3 Preguntar Puesto').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]}, "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('S1.3 Preguntar Puesto').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# Error Name
error_name_js = r"""const trigger = $('Trigger from Dispatcher').first().json;
const errMsg = $('S1 Validar Nombre').first().json.validation.error_message;
const msgText = errMsg + '\n\n\u00bfCu\u00e1l es tu nombre completo?';
const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: msgText }] }] };
return [{ json: { ...trigger, patch_body_string: JSON.stringify(patchBody) } }];"""
add_node("at-s1-error", "S1.E Build Error Nombre", "code", 2, [-1248, -16], {"jsCode": error_name_js})

add_node("at-s1-err-patch", "S1.E1 PATCH Error Nombre", "httpRequest", 4.2, [-1008, -16], {
    "method": "PATCH", "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}, {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ $json.patch_body_string }}", "options": {}
}, continueOnFail=True)

add_node("at-s1-err-salesbot", "S1.E2 Salesbot Error Nombre", "httpRequest", 4.2, [-752, -16], {
    "method": "POST", "url": "={{ $('S1.E Build Error Nombre').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S1.E Build Error Nombre').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'S1.E Build Error Nombre\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

add_node("wait-at-s1e", "Wait 2s S1E", "wait", 1.1, [-640, -16], {"amount": 2})

add_node("at-s1-err-clear", "S1.E3 Clear Error Nombre", "httpRequest", 4.2, [-528, -16], {
    "method": "PATCH", "url": "={{ $('S1.E Build Error Nombre').item.json.kommo_dominio }}/api/v4/leads/{{ $('S1.E Build Error Nombre').item.json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S1.E Build Error Nombre').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]}, "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('S1.E Build Error Nombre').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# ── 25-37. Step 2: Validate Puesto + Transition + Q1 ──
validate_puesto_js = """const text = ($json.message_text || '').trim();
const isValid = text.length >= 2;
return [{ json: { ...$json, validation: { valid: isValid, value: isValid ? text : null,
  error_message: isValid ? '' : '\u26a0\ufe0f Por favor escribe tu puesto actual.' } } }];"""
add_node("at-s2-validate", "S2 Validar Puesto", "code", 2, [-1600, 320], {"jsCode": validate_puesto_js})

add_node("at-s2-valid-check", "S2.1 Puesto V\u00e1lido?", "if", 2.2, [-1376, 320], {
    "conditions": {"options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "puesto-valid", "leftValue": "={{ $json.validation.valid }}",
                        "rightValue": True, "operator": {"type": "boolean", "operation": "equals"}}],
        "combinator": "and"}, "options": {}
})

add_node("at-s2-save", "S2.2 Guardar Puesto", "dataTable", 1.1, [-1152, 192], {
    "operation": "update",
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "list", "cachedResultName": "sessions"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $json.contact_id }}"}]},
    "columns": {
        "mappingMode": "defineBelow",
        "value": {"jobPosition": "={{ $json.validation.value }}", "current_step": "=3", "last_interaction": "={{ $now.toISO() }}"},
        "matchingColumns": [], "schema": [schema_field("phone_number"), schema_field("jobPosition"), schema_field("current_step", "number"), schema_field("last_interaction")],
        "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# Build Transition + Q1
transition_js = r"""const trigger = $('Trigger from Dispatcher').first().json;
const q1Text = '\u00a1Perfecto! \ud83d\ude80 Vamos a comenzar.\n\nSon 10 preguntas r\u00e1pidas. Para cada una elige la opci\u00f3n que m\u00e1s se parezca a lo que t\u00fa har\u00edas en la vida real.\n\nResponde siempre con la letra de tu opci\u00f3n: *A*, *B* o *C*\n\n\u00a1Empecemos! \ud83d\udc47\n\n*Pregunta 1 de 10* \ud83c\udf10\n\nSi te piden trabajar en un archivo con un compa\u00f1ero al mismo tiempo, t\u00fa:\n\nA) Me confundo. Prefiero hacerlo yo solo y mandarlo luego por correo.\nB) S\u00e9 que se puede por internet, pero me da miedo que alguien borre mi parte.\nC) \u00a1Me encanta! Uso herramientas en la "Nube" para que avancemos juntos en vivo.\n\n\u2192 Responde con la letra: *A*, *B* o *C*';
const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: q1Text }] }] };
return [{ json: { ...trigger, patch_body_string: JSON.stringify(patchBody) } }];"""
add_node("at-s2-transition", "S2.3 Build Transici\u00f3n + Q1", "code", 2, [-928, 192], {"jsCode": transition_js})

add_node("at-s2-patch", "S2.4 PATCH Transici\u00f3n", "httpRequest", 4.2, [-704, 192], {
    "method": "PATCH", "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}, {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ $json.patch_body_string }}", "options": {}
}, continueOnFail=True)

add_node("at-s2-salesbot", "S2.5 Salesbot Transici\u00f3n", "httpRequest", 4.2, [-480, 192], {
    "method": "POST", "url": "={{ $('S2.3 Build Transici\u00f3n + Q1').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S2.3 Build Transici\u00f3n + Q1').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'S2.3 Build Transici\\u00f3n + Q1\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

add_node("wait-at-s2", "Wait 2s S2", "wait", 1.1, [-368, 192], {"amount": 2})

add_node("at-s2-clear", "S2.6 Clear Salesbot Transicion", "httpRequest", 4.2, [-256, 192], {
    "method": "PATCH", "url": "={{ $('S2.3 Build Transici\u00f3n + Q1').item.json.kommo_dominio }}/api/v4/leads/{{ $('S2.3 Build Transici\u00f3n + Q1').item.json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S2.3 Build Transici\u00f3n + Q1').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]}, "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('S2.3 Build Transici\u00f3n + Q1').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# Error Puesto
error_puesto_js = r"""const trigger = $('Trigger from Dispatcher').first().json;
const errMsg = $('S2 Validar Puesto').first().json.validation.error_message;
const msgText = errMsg + '\n\n\u00bfCu\u00e1l es tu puesto actual?';
const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: msgText }] }] };
return [{ json: { ...trigger, patch_body_string: JSON.stringify(patchBody) } }];"""
add_node("at-s2-error", "S2.E Build Error Puesto", "code", 2, [-1136, 400], {"jsCode": error_puesto_js})

add_node("at-s2-err-patch", "S2.E1 PATCH Error Puesto", "httpRequest", 4.2, [-912, 400], {
    "method": "PATCH", "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}, {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ $json.patch_body_string }}", "options": {}
}, continueOnFail=True)

add_node("at-s2-err-salesbot", "S2.E2 Salesbot Error Puesto", "httpRequest", 4.2, [-688, 400], {
    "method": "POST", "url": "={{ $('S2.E Build Error Puesto').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S2.E Build Error Puesto').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]}, "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'S2.E Build Error Puesto\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

add_node("wait-at-s2e", "Wait 2s S2E", "wait", 1.1, [-576, 400], {"amount": 2})

add_node("at-s2-err-clear", "S2.E3 Clear Error Puesto", "httpRequest", 4.2, [-464, 400], {
    "method": "PATCH", "url": "={{ $('S2.E Build Error Puesto').item.json.kommo_dominio }}/api/v4/leads/{{ $('S2.E Build Error Puesto').item.json.lead_id }}",
    "sendHeaders": True, "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('S2.E Build Error Puesto').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]}, "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('S2.E Build Error Puesto').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]}, "options": {}
}, continueOnFail=True)

# ── Connections ──
connect("Trigger from Dispatcher", "AT.1 Check Session")
connect("AT.1 Check Session", "AT.2 Handle Session")
connect("AT.2 Handle Session", "AT.3 Session Exists?")
connect("AT.3 Session Exists?", "AT.6 Router por Step", 0)        # TRUE
connect("AT.3 Session Exists?", "AT.4 Create New Session", 1)     # FALSE

# New session branch
connect("AT.4 Create New Session", "AT.4b Create AT Responses")
connect("AT.4b Create AT Responses", "AT.5 Build Welcome")
connect("AT.5 Build Welcome", "AT.5a PATCH Welcome")
connect("AT.5a PATCH Welcome", "AT.5b Salesbot Welcome 1")
connect("AT.5b Salesbot Welcome 1", "Wait 2s W1")
connect("Wait 2s W1", "AT.5c Clear Welcome 1")
connect("AT.5c Clear Welcome 1", "AT.5d PATCH Welcome 2")
connect("AT.5d PATCH Welcome 2", "AT.5e Salesbot Welcome 2")
connect("AT.5e Salesbot Welcome 2", "Wait 2s W2")
connect("Wait 2s W2", "AT.5f Clear Welcome 2")

# Existing session: Router
connect("AT.6 Router por Step", "S1 Validar Nombre", 0)           # step 1
connect("AT.6 Router por Step", "S2 Validar Puesto", 1)           # step 2
connect("AT.6 Router por Step", "AT.7 Call AT Process Question", 2) # step >= 3

# Step 1: Name
connect("S1 Validar Nombre", "S1.1 Nombre V\u00e1lido?")
connect("S1.1 Nombre V\u00e1lido?", "S1.2 Guardar Nombre", 0)    # TRUE
connect("S1.1 Nombre V\u00e1lido?", "S1.E Build Error Nombre", 1) # FALSE
connect("S1.2 Guardar Nombre", "S1.3 Preguntar Puesto")
connect("S1.3 Preguntar Puesto", "S1.4 PATCH Pregunta Puesto")
connect("S1.4 PATCH Pregunta Puesto", "S1.5 Salesbot Puesto")
connect("S1.5 Salesbot Puesto", "Wait 2s S1")
connect("Wait 2s S1", "S1.6 Clear Salesbot Puesto")
connect("S1.E Build Error Nombre", "S1.E1 PATCH Error Nombre")
connect("S1.E1 PATCH Error Nombre", "S1.E2 Salesbot Error Nombre")
connect("S1.E2 Salesbot Error Nombre", "Wait 2s S1E")
connect("Wait 2s S1E", "S1.E3 Clear Error Nombre")

# Step 2: Puesto
connect("S2 Validar Puesto", "S2.1 Puesto V\u00e1lido?")
connect("S2.1 Puesto V\u00e1lido?", "S2.2 Guardar Puesto", 0)    # TRUE
connect("S2.1 Puesto V\u00e1lido?", "S2.E Build Error Puesto", 1) # FALSE
connect("S2.2 Guardar Puesto", "S2.3 Build Transici\u00f3n + Q1")
connect("S2.3 Build Transici\u00f3n + Q1", "S2.4 PATCH Transici\u00f3n")
connect("S2.4 PATCH Transici\u00f3n", "S2.5 Salesbot Transici\u00f3n")
connect("S2.5 Salesbot Transici\u00f3n", "Wait 2s S2")
connect("Wait 2s S2", "S2.6 Clear Salesbot Transicion")
connect("S2.E Build Error Puesto", "S2.E1 PATCH Error Puesto")
connect("S2.E1 PATCH Error Puesto", "S2.E2 Salesbot Error Puesto")
connect("S2.E2 Salesbot Error Puesto", "Wait 2s S2E")
connect("Wait 2s S2E", "S2.E3 Clear Error Puesto")

# ── Output ──
workflow = {
    "name": "[Skillera] Chatbot AT",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner"}
}

with open("/tmp/chatbot_at.json", "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=True)

print(f"Workflow JSON written: {len(nodes)} nodes, {sum(len(v) for outs in connections.values() for v in outs.get('main', []))} connections")
