"""
Generate the [Skillera] AT Process Question workflow JSON for n8n.
Replicates the IE Process Question pattern but adapted for AT test:
- Validates A/B/C instead of 1-4
- Hardcodes questions (no DataTable lookup)
- Uses at_responses table (B4pPUen5ysuETffw)
- Calls Calculate AT Scores (p0rkK6Ft0UWzzeFI)
"""
import json

# ── Constants ──
AT_RESPONSES_TABLE = "B4pPUen5ysuETffw"
SESSIONS_TABLE = "tBaZMEOVw2tvcswf"
CALCULATE_AT_SCORES_WF = "p0rkK6Ft0UWzzeFI"
BOT_ID = 64784  # Same salesbot as IE

# ── Helper: schema field ──
def schema_field(name, ftype="string", read_only=False):
    return {
        "id": name, "displayName": name, "required": False,
        "defaultMatch": False, "display": True, "type": ftype,
        "readOnly": read_only, "removed": False
    }

def schema_field_exec(name, ftype="string"):
    return {
        "id": name, "displayName": name, "required": False,
        "defaultMatch": False, "display": True, "canBeUsedToMatch": True,
        "type": ftype, "removed": False
    }

# ── Questions hardcoded ──
QUESTIONS_JS = r'''const QUESTIONS = {
  3: '*Pregunta 1 de 10* \ud83c\udf10\n\nSi te piden trabajar en un archivo con un compa\u00f1ero al mismo tiempo, t\u00fa:\n\nA) Me confundo. Prefiero hacerlo yo solo y mandarlo luego por correo.\nB) S\u00e9 que se puede por internet, pero me da miedo que alguien borre mi parte.\nC) \u00a1Me encanta! Uso herramientas en la "Nube" para que avancemos juntos en vivo.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  4: '*Pregunta 2 de 10* \ud83c\udf10\n\n\u00bfSabes c\u00f3mo se conectan dos aplicaciones? (Ejemplo: que tu app de comida sepa d\u00f3nde est\u00e1 el repartidor):\n\nA) No tengo idea de c\u00f3mo pasa eso.\nB) He o\u00eddo que existen "puentes" (llamados APIs), pero no s\u00e9 c\u00f3mo funcionan.\nC) Entiendo que los sistemas se hablan entre s\u00ed para darnos informaci\u00f3n r\u00e1pida.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  5: '*Pregunta 3 de 10* \ud83d\udee1\ufe0f\n\nTe llega un correo "urgente" de tu banco o jefe pidiendo tu contrase\u00f1a, \u00bfqu\u00e9 haces?\n\nA) Entro al link y la pongo r\u00e1pido para no tener problemas.\nB) Sospecho un poco, pero si el correo se ve real, termino entrando.\nC) \u00a1Alerta! S\u00e9 que es un enga\u00f1o (Phishing) y lo borro de inmediato.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  6: '*Pregunta 4 de 10* \ud83d\udee1\ufe0f\n\n\u00bfQu\u00e9 es para ti la "Verificaci\u00f3n en dos pasos" (el c\u00f3digo extra que llega al cel)?\n\nA) Algo muy molesto que me quita tiempo para entrar a mis cuentas.\nB) Lo tengo en algunas cosas, pero no entiendo bien para qu\u00e9 sirve.\nC) Mi seguro de vida digital; es la barrera que evita que me roben mi identidad.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  7: '*Pregunta 5 de 10* \ud83e\udd16\n\nSobre la Inteligencia Artificial (como ChatGPT), t\u00fa piensas que:\n\nA) Es cosa de pel\u00edculas o algo que solo los ingenieros usan.\nB) Es para que los estudiantes hagan trampa en sus tareas.\nC) Es mi asistente personal para redactar correos, planear y ahorrarme horas.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  8: '*Pregunta 6 de 10* \ud83e\udd16\n\nSi tienes que hacer una tarea dif\u00edcil o un reporte largo:\n\nA) Me resigno a pasar horas haci\u00e9ndolo a mano como siempre.\nB) Busco en Google ejemplos para copiar y pegar un poco.\nC) Uso Inteligencia Artificial para que me ayude con ideas y estructura.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  9: '*Pregunta 7 de 10* \u26a1\n\nEl mundo hoy cambia muy r\u00e1pido. Si en tu trabajo te cambian las reglas hoy:\n\nA) Me estreso y me cuesta mucho soltar mi forma anterior de trabajar.\nB) Me adapto, pero me siento perdido y con mucho miedo a equivocarme.\nC) Entiendo que el cambio es normal y busco r\u00e1pido c\u00f3mo aprender lo nuevo.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  10: '*Pregunta 8 de 10* \u26a1\n\n\u00bfSabes qu\u00e9 es trabajar en un "Sprint" o usar un tablero de tareas (Kanban)?\n\nA) No, yo prefiero mi lista en papel o confiar en mi memoria.\nB) He visto los tableros con etiquetas de colores, pero no s\u00e9 usarlos.\nC) S\u00ed, me sirven para ver qu\u00e9 est\u00e1 pendiente, qu\u00e9 va en proceso y qu\u00e9 ya termin\u00e9.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  11: '*Pregunta 9 de 10* \ud83e\udde0\n\nSi encuentras un error en el sistema de la empresa que te deja ver datos de otros:\n\nA) No digo nada, no es mi problema.\nB) Me da curiosidad y reviso un poco antes de avisar.\nC) Aviso de inmediato porque entiendo que la privacidad es sagrada.\n\n\u2192 Responde con la letra: *A*, *B* o *C*',
  12: '*Pregunta 10 de 10* \ud83e\udde0\n\n\u00bfC\u00f3mo ves tu futuro profesional con tanta tecnolog\u00eda?\n\nA) Tengo miedo de que las m\u00e1quinas me quiten mi trabajo.\nB) Creo que nada va a cambiar y seguir\u00e9 trabajando igual que siempre.\nC) S\u00e9 que si aprendo a usar estas herramientas, tendr\u00e9 mejores puestos y sueldos.\n\n\u2192 Responde con la letra: *A*, *B* o *C*'
};'''

# ── Nodes ──
nodes = []
connections = {}

def add_node(nid, name, ntype, ver, pos, params, **extra):
    node = {"id": nid, "name": name, "type": f"n8n-nodes-base.{ntype}", "typeVersion": ver, "position": pos, "parameters": params}
    node.update(extra)
    nodes.append(node)

def connect(src_name, dst_name, src_output=0, dst_input=0):
    if src_name not in connections:
        connections[src_name] = {"main": []}
    main = connections[src_name]["main"]
    while len(main) <= src_output:
        main.append([])
    main[src_output].append({"node": dst_name, "type": "main", "index": dst_input})

# 1. Trigger
add_node("at-pq-trigger", "Trigger from Main", "executeWorkflowTrigger", 1.1, [-1600, 400], {
    "inputSource": "jsonExample",
    "jsonExample": json.dumps({
        "message_text": "B", "contact_id": "36013062", "entity_id": "34667542",
        "lead_id": "34667542", "current_step": 3,
        "kommo_field_id": "2263666", "kommo_token": "TOKEN",
        "kommo_dominio": "https://example.kommo.com"
    }, indent=2)
})

# 2. Validate A/B/C
validate_js = """const text = ($json.message_text || '').toUpperCase().trim();
const currentStep = $json.current_step;
const isValid = ['A', 'B', 'C'].includes(text);
const questionNumber = currentStep - 2;
const questionKey = `q${questionNumber}`;
return [{ json: {
  ...$json,
  validation: {
    valid: isValid,
    value: isValid ? text : null,
    field: questionKey,
    error_message: isValid ? '' : '\u26a0\ufe0f Respuesta no v\u00e1lida. Por favor responde solo con la letra: *A*, *B* o *C*'
  },
  question_number: questionNumber,
  question_key: questionKey
} }];"""
add_node("at-pq-validate", "AT.PQ.1 Validate A/B/C", "code", 2, [-1376, 400], {"jsCode": validate_js})

# 3. Valid? IF
add_node("at-pq-valid-check", "AT.PQ.2 Valid?", "if", 2.2, [-1152, 400], {
    "conditions": {
        "options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "valid-check", "leftValue": "={{ $json.validation.valid }}", "rightValue": True, "operator": {"type": "boolean", "operation": "equals"}}],
        "combinator": "and"
    }, "options": {}
})

# 4. Prepare Save
save_prep_js = """const currentStep = parseInt($json.current_step, 10);
const answer = $json.validation.value;
const contactId = $json.contact_id;
const questionKey = $json.question_key;
const isFirstQuestion = currentStep === 3;
if (isFirstQuestion) {
  return [{ json: { ...$json, save_action: 'insert', save_data: { phone_number: contactId, q1: answer, q2: '', q3: '', q4: '', q5: '', q6: '', q7: '', q8: '', q9: '', q10: '' } } }];
} else {
  return [{ json: { ...$json, save_action: 'update', save_data: { phone_number: contactId, question_key: questionKey, answer: answer } } }];
}"""
add_node("at-pq-save-prep", "AT.PQ.3 Prepare Save", "code", 2, [-928, 304], {"jsCode": save_prep_js})

# 5. First Question? IF
add_node("at-pq-first-check", "AT.PQ.4 First Question?", "if", 2.2, [-704, 304], {
    "conditions": {
        "options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "is-insert", "leftValue": "={{ $json.save_action }}", "rightValue": "insert", "operator": {"type": "string", "operation": "equals"}}],
        "combinator": "and"
    }, "options": {}
})

# 6. Insert First Response (DataTable)
q_schema = [schema_field("phone_number")] + [schema_field(f"q{i}") for i in range(1, 11)]
q_value = {"phone_number": "={{ $json.save_data.phone_number }}"}
for i in range(1, 11):
    q_value[f"q{i}"] = "={{ $json.save_data.q" + str(i) + " }}"

add_node("at-pq-insert", "AT.PQ.5 Insert First Response", "dataTable", 1.1, [-480, 160], {
    "dataTableId": {"__rl": True, "value": AT_RESPONSES_TABLE, "mode": "id"},
    "columns": {
        "mappingMode": "defineBelow", "value": q_value, "matchingColumns": [],
        "schema": q_schema, "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# 7. Get Existing Responses (DataTable)
add_node("at-pq-get-existing", "AT.PQ.6 Get Existing Responses", "dataTable", 1.1, [-480, 400], {
    "operation": "get",
    "dataTableId": {"__rl": True, "value": AT_RESPONSES_TABLE, "mode": "id"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $('AT.PQ.3 Prepare Save').first().json.contact_id }}"}]},
    "limit": 1
}, alwaysOutputData=True)

# 8. Merge & Update
merge_js = """const existing = $json;
const saveData = $('AT.PQ.3 Prepare Save').first().json.save_data;
const questionKey = saveData.question_key;
const answer = saveData.answer;
const merged = {
  q1: questionKey==='q1' ? answer : (existing.q1 || ''),
  q2: questionKey==='q2' ? answer : (existing.q2 || ''),
  q3: questionKey==='q3' ? answer : (existing.q3 || ''),
  q4: questionKey==='q4' ? answer : (existing.q4 || ''),
  q5: questionKey==='q5' ? answer : (existing.q5 || ''),
  q6: questionKey==='q6' ? answer : (existing.q6 || ''),
  q7: questionKey==='q7' ? answer : (existing.q7 || ''),
  q8: questionKey==='q8' ? answer : (existing.q8 || ''),
  q9: questionKey==='q9' ? answer : (existing.q9 || ''),
  q10: questionKey==='q10' ? answer : (existing.q10 || '')
};
return [{ json: { ...$('AT.PQ.3 Prepare Save').first().json, update_data: { phone_number: saveData.phone_number, ...merged } } }];"""
add_node("at-pq-merge", "AT.PQ.7 Merge & Update", "code", 2, [-256, 400], {"jsCode": merge_js})

# 9. Update Responses (DataTable)
update_q_value = {}
for i in range(1, 11):
    update_q_value[f"q{i}"] = "={{ $json.update_data.q" + str(i) + " }}"

add_node("at-pq-update-dt", "AT.PQ.8 Update Responses", "dataTable", 1.1, [-32, 400], {
    "operation": "update",
    "dataTableId": {"__rl": True, "value": AT_RESPONSES_TABLE, "mode": "id"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $json.update_data.phone_number }}"}]},
    "columns": {
        "mappingMode": "defineBelow", "value": update_q_value, "matchingColumns": [],
        "schema": q_schema, "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# 10. Update Session Step (DataTable)
session_schema = [schema_field("phone_number"), schema_field("current_step", "number"), schema_field("last_interaction")]
add_node("at-pq-update-session", "AT.PQ.9 Update Session Step", "dataTable", 1.1, [192, 304], {
    "operation": "update",
    "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "id"},
    "filters": {"conditions": [{"keyName": "phone_number", "keyValue": "={{ $('Trigger from Main').first().json.contact_id }}"}]},
    "columns": {
        "mappingMode": "defineBelow",
        "value": {"current_step": "={{ $('Trigger from Main').first().json.current_step + 1 }}", "last_interaction": "={{ $now.toISO() }}"},
        "matchingColumns": [], "schema": session_schema,
        "attemptToConvertTypes": False, "convertFieldsToString": False
    }, "options": {}
})

# 11. Is Last Question? IF (step >= 12)
add_node("at-pq-is-last", "AT.PQ.9a Is Last Question?", "if", 2.2, [416, 304], {
    "conditions": {
        "options": {"version": 2, "leftValue": "", "caseSensitive": True, "typeValidation": "strict"},
        "conditions": [{"id": "is-last", "leftValue": "={{ parseInt($('Trigger from Main').first().json.current_step, 10) }}", "rightValue": 12, "operator": {"type": "number", "operation": "gte"}}],
        "combinator": "and"
    }, "options": {}
})

# 12. Build Completion Message
completion_js = """const trigger = $('Trigger from Main').first().json;
return [{ json: {
  response_text: '\u00a1Gracias por completar el test! \ud83c\udfaf\\n\\nEstoy generando tu diagn\u00f3stico personalizado, en unos segundos lo recibir\u00e1s aqu\u00ed mismo... \u23f3',
  is_last_question: true,
  contact_id: trigger.contact_id,
  entity_id: trigger.entity_id,
  lead_id: trigger.lead_id,
  kommo_field_id: trigger.kommo_field_id,
  kommo_token: trigger.kommo_token,
  kommo_dominio: trigger.kommo_dominio
} }];"""
add_node("at-pq-build-completion", "AT.PQ.10a Build Completion", "code", 2, [640, 176], {"jsCode": completion_js})

# 13. Build Next Question (hardcoded)
next_q_js = QUESTIONS_JS + """
const trigger = $('Trigger from Main').first().json;
const nextStep = trigger.current_step + 1;
const msgText = QUESTIONS[nextStep] || 'Error: pregunta no encontrada';
const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: msgText }] }] };
return [{ json: {
  response_text: msgText,
  is_last_question: false,
  patch_body_string: JSON.stringify(patchBody),
  contact_id: trigger.contact_id,
  entity_id: trigger.entity_id,
  lead_id: trigger.lead_id,
  kommo_field_id: trigger.kommo_field_id,
  kommo_token: trigger.kommo_token,
  kommo_dominio: trigger.kommo_dominio
} }];"""
add_node("at-pq-get-next-q", "AT.PQ.10 Build Next Question", "code", 2, [640, 400], {"jsCode": next_q_js})

# 14. PATCH Next Question
add_node("at-pq-patch-next", "AT.PQ.11 PATCH Next Question", "httpRequest", 4.2, [880, 400], {
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

# 15. Salesbot Next
add_node("at-pq-salesbot-next", "AT.PQ.12 Salesbot Next", "httpRequest", 4.2, [1088, 400], {
    "method": "POST",
    "url": "={{ $('AT.PQ.10 Build Next Question').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.PQ.10 Build Next Question').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'AT.PQ.10 Build Next Question\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

# 16. Wait 2s PQ Next
add_node("wait-pq-next", "Wait 2s PQ Next", "wait", 1.1, [1280, 400], {"amount": 2})

# 17. Clear PQ Next
add_node("clear-pq-next", "Clear PQ Next", "httpRequest", 4.2, [1472, 400], {
    "method": "PATCH",
    "url": "={{ $('AT.PQ.10 Build Next Question').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.PQ.10 Build Next Question').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.PQ.10 Build Next Question').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]},
    "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('AT.PQ.10 Build Next Question').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]},
    "options": {}
}, continueOnFail=True)

# 18. PATCH Completion
add_node("at-pq-patch-completion", "AT.PQ.10b PATCH Completion", "httpRequest", 4.2, [864, 176], {
    "method": "PATCH",
    "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
    "body": "={{ JSON.stringify({custom_fields_values: [{field_id: parseInt($json.kommo_field_id), values: [{value: $json.response_text}]}]}) }}",
    "options": {}
}, continueOnFail=True)

# 19. Salesbot Completion
add_node("at-pq-salesbot-completion", "AT.PQ.10c Salesbot Completion", "httpRequest", 4.2, [1088, 176], {
    "method": "POST",
    "url": "={{ $('AT.PQ.10a Build Completion').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.PQ.10a Build Completion').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'AT.PQ.10a Build Completion\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

# 20. Wait 2s Completion
add_node("wait-pq-completion", "Wait 2s PQ Completion", "wait", 1.1, [1280, 176], {"amount": 2})

# 21. Clear Completion
add_node("clear-pq-completion", "Clear PQ Completion", "httpRequest", 4.2, [1456, 176], {
    "method": "PATCH",
    "url": "={{ $('AT.PQ.10a Build Completion').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.PQ.10a Build Completion').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.PQ.10a Build Completion').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]},
    "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('AT.PQ.10a Build Completion').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]},
    "options": {}
}, continueOnFail=True)

# 22. Prep Scores Payload
scores_prep_js = """const src = $('AT.PQ.10a Build Completion').first().json;
return [{ json: {
  contact_id: src.contact_id,
  entity_id: src.entity_id,
  lead_id: src.lead_id,
  kommo_field_id: src.kommo_field_id,
  kommo_token: src.kommo_token,
  kommo_dominio: src.kommo_dominio
} }];"""
add_node("at-pq-prep-scores", "AT.PQ.10d Prep Scores Payload", "code", 2, [1616, 176], {"jsCode": scores_prep_js})

# 23. Call Calculate AT Scores
scores_schema = [schema_field_exec(f) for f in ["contact_id", "entity_id", "lead_id", "kommo_field_id", "kommo_token", "kommo_dominio"]]
scores_value = {f: "={{ $('AT.PQ.10d Prep Scores Payload').first().json." + f + " }}" for f in ["contact_id", "entity_id", "lead_id", "kommo_field_id", "kommo_token", "kommo_dominio"]}
scores_value["kommo_field_id"] = "={{ String($('AT.PQ.10d Prep Scores Payload').first().json.kommo_field_id) }}"

add_node("at-pq-call-scores", "AT.PQ.10e Call Calculate AT Scores", "executeWorkflow", 1.2, [1856, 176], {
    "workflowId": {"__rl": True, "value": CALCULATE_AT_SCORES_WF, "mode": "id"},
    "workflowInputs": {
        "mappingMode": "defineBelow", "value": scores_value,
        "matchingColumns": [], "schema": scores_schema,
        "attemptToConvertTypes": False, "convertFieldsToString": True
    }, "options": {}
})

# ── Error branch ──
# 24. Build Error (with hardcoded question for retry)
error_js = QUESTIONS_JS + """
const trigger = $('Trigger from Main').first().json;
const validation = $('AT.PQ.1 Validate A/B/C').first().json.validation;
const currentStep = trigger.current_step;
const currentQ = QUESTIONS[currentStep] || 'Error: pregunta no encontrada';
const msgText = validation.error_message + '\\n\\n' + currentQ;
const patchBody = { custom_fields_values: [{ field_id: parseInt(trigger.kommo_field_id), values: [{ value: msgText }] }] };
return [{ json: {
  patch_body_string: JSON.stringify(patchBody),
  contact_id: trigger.contact_id,
  entity_id: trigger.entity_id,
  lead_id: trigger.lead_id,
  kommo_field_id: trigger.kommo_field_id,
  kommo_token: trigger.kommo_token,
  kommo_dominio: trigger.kommo_dominio
} }];"""
add_node("at-pq-err-build", "AT.PQ.E1 Build Error", "code", 2, [-928, 608], {"jsCode": error_js})

# 25. PATCH Error
add_node("at-pq-err-patch", "AT.PQ.E2 PATCH Error", "httpRequest", 4.2, [-704, 608], {
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

# 26. Salesbot Error
add_node("at-pq-err-salesbot", "AT.PQ.E3 Salesbot Error", "httpRequest", 4.2, [-480, 608], {
    "method": "POST",
    "url": "={{ $('AT.PQ.E1 Build Error').item.json.kommo_dominio }}/api/v2/salesbot/run",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.PQ.E1 Build Error').item.json.kommo_token }}"},
        {"name": "accept", "value": "application/json"}
    ]},
    "sendBody": True, "specifyBody": "json",
    "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'AT.PQ.E1 Build Error\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
    "options": {}
}, continueOnFail=True)

# 27. Wait 2s Error
add_node("wait-pq-error", "Wait 2s PQ Error", "wait", 1.1, [-256, 608], {"amount": 2})

# 28. Clear Error
add_node("clear-pq-error", "Clear PQ Error", "httpRequest", 4.2, [-32, 608], {
    "method": "PATCH",
    "url": "={{ $('AT.PQ.E1 Build Error').item.json.kommo_dominio }}/api/v4/leads/{{ $('AT.PQ.E1 Build Error').item.json.lead_id }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "authorization", "value": "=Bearer {{ $('AT.PQ.E1 Build Error').item.json.kommo_token }}"},
        {"name": "content-type", "value": "application/json"}
    ]},
    "sendBody": True,
    "bodyParameters": {"parameters": [
        {"name": "custom_fields_values", "value": "={{ [{field_id: parseInt($('AT.PQ.E1 Build Error').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
    ]},
    "options": {}
}, continueOnFail=True)

# ── Connections ──
connect("Trigger from Main", "AT.PQ.1 Validate A/B/C")
connect("AT.PQ.1 Validate A/B/C", "AT.PQ.2 Valid?")
connect("AT.PQ.2 Valid?", "AT.PQ.3 Prepare Save", 0)        # TRUE
connect("AT.PQ.2 Valid?", "AT.PQ.E1 Build Error", 1)         # FALSE
connect("AT.PQ.3 Prepare Save", "AT.PQ.4 First Question?")
connect("AT.PQ.4 First Question?", "AT.PQ.5 Insert First Response", 0)  # TRUE (insert)
connect("AT.PQ.4 First Question?", "AT.PQ.6 Get Existing Responses", 1) # FALSE (update)
connect("AT.PQ.5 Insert First Response", "AT.PQ.9 Update Session Step")
connect("AT.PQ.6 Get Existing Responses", "AT.PQ.7 Merge & Update")
connect("AT.PQ.7 Merge & Update", "AT.PQ.8 Update Responses")
connect("AT.PQ.8 Update Responses", "AT.PQ.9 Update Session Step")
connect("AT.PQ.9 Update Session Step", "AT.PQ.9a Is Last Question?")
connect("AT.PQ.9a Is Last Question?", "AT.PQ.10a Build Completion", 0)  # TRUE (last)
connect("AT.PQ.9a Is Last Question?", "AT.PQ.10 Build Next Question", 1) # FALSE (not last)
connect("AT.PQ.10a Build Completion", "AT.PQ.10b PATCH Completion")
connect("AT.PQ.10b PATCH Completion", "AT.PQ.10c Salesbot Completion")
connect("AT.PQ.10c Salesbot Completion", "Wait 2s PQ Completion")
connect("Wait 2s PQ Completion", "Clear PQ Completion")
connect("Clear PQ Completion", "AT.PQ.10d Prep Scores Payload")
connect("AT.PQ.10d Prep Scores Payload", "AT.PQ.10e Call Calculate AT Scores")
connect("AT.PQ.10 Build Next Question", "AT.PQ.11 PATCH Next Question")
connect("AT.PQ.11 PATCH Next Question", "AT.PQ.12 Salesbot Next")
connect("AT.PQ.12 Salesbot Next", "Wait 2s PQ Next")
connect("Wait 2s PQ Next", "Clear PQ Next")
connect("AT.PQ.E1 Build Error", "AT.PQ.E2 PATCH Error")
connect("AT.PQ.E2 PATCH Error", "AT.PQ.E3 Salesbot Error")
connect("AT.PQ.E3 Salesbot Error", "Wait 2s PQ Error")
connect("Wait 2s PQ Error", "Clear PQ Error")

# ── Output ──
workflow = {
    "name": "[Skillera] AT Process Question",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner"}
}

with open("/tmp/at_process_question.json", "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=True)

print(f"Workflow JSON written: {len(nodes)} nodes, {sum(len(v) for outs in connections.values() for v in outs.get('main', []))} connections")
print("File: /tmp/at_process_question.json")
