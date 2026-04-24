"""
Fix AT Process Question: adjust step mapping for 11-step flow.
- question_number = current_step - 1 (not - 2)
- question_key = q{step-1}
- First question at step 2 (not 3)
- Last question at step 11 (not 12)
- QUESTIONS map: step 2-11 (not 3-12)
"""
import json, urllib.request, ssl

N8N_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMDYyOGNmYi04MGYxLTQwMjUtYmE1MC02ZDJkZWZjNmY4ZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiN2MxMTM5ZTYtNzQ2OS00ZTAwLThkODMtZDRkODcyNjEwNzNhIiwiaWF0IjoxNzcyNjAyOTk5fQ.XbXiBQztJgmH07BPqlO1HCX2iGpm6klvVpQ378WozKM'
ctx = ssl.create_default_context()
WF_ID = '8cv7GiAK6nIOLpXM'

# Get current workflow
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}'
req = urllib.request.Request(url)
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
wf = json.loads(resp.read().decode())
print(f'Got AT Process Question: {len(wf["nodes"])} nodes')

# Fix each node
for node in wf['nodes']:
    nid = node['id']
    params = node.get('parameters', {})

    # Fix validate: question_number = step - 1
    if nid == 'at-pq-validate':
        params['jsCode'] = """const text = ($json.message_text || '').toUpperCase().trim();
const currentStep = $json.current_step;
const isValid = ['A', 'B', 'C'].includes(text);
const questionNumber = currentStep - 1;
const questionKey = `q${questionNumber}`;
return [{ json: {
  ...$json,
  validation: {
    valid: isValid,
    value: isValid ? text : null,
    field: questionKey,
    error_message: isValid ? '' : '\\u26a0\\ufe0f Respuesta no v\\u00e1lida. Por favor responde solo con la letra: *A*, *B* o *C*'
  },
  question_number: questionNumber,
  question_key: questionKey
} }];"""
        print('  Fixed: AT.PQ.1 Validate (step - 1)')

    # Fix prepare save: first question at step 2
    if nid == 'at-pq-save-prep':
        params['jsCode'] = """const currentStep = parseInt($json.current_step, 10);
const answer = $json.validation.value;
const contactId = $json.contact_id;
const questionKey = $json.question_key;
const isFirstQuestion = currentStep === 2;
if (isFirstQuestion) {
  return [{ json: { ...$json, save_action: 'insert', save_data: { phone_number: contactId, q1: answer, q2: '', q3: '', q4: '', q5: '', q6: '', q7: '', q8: '', q9: '', q10: '' } } }];
} else {
  return [{ json: { ...$json, save_action: 'update', save_data: { phone_number: contactId, question_key: questionKey, answer: answer } } }];
}"""
        print('  Fixed: AT.PQ.3 Prepare Save (first at step 2)')

    # Fix is last question: step >= 11
    if nid == 'at-pq-is-last':
        params['conditions']['conditions'][0]['rightValue'] = 11
        print('  Fixed: AT.PQ.9a Is Last Question (>= 11)')

    # Fix build next question: QUESTIONS map step 2-11
    if nid == 'at-pq-get-next-q':
        params['jsCode'] = """const QUESTIONS = {
  2: '*Pregunta 1 de 10* \\ud83c\\udf10\\n\\nSi te piden trabajar en un archivo con un compa\\u00f1ero al mismo tiempo, t\\u00fa:\\n\\nA) Me confundo. Prefiero hacerlo yo solo y mandarlo luego por correo.\\nB) S\\u00e9 que se puede por internet, pero me da miedo que alguien borre mi parte.\\nC) \\u00a1Me encanta! Uso herramientas en la "Nube" para que avancemos juntos en vivo.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  3: '*Pregunta 2 de 10* \\ud83c\\udf10\\n\\n\\u00bfSabes c\\u00f3mo se conectan dos aplicaciones? (Ejemplo: que tu app de comida sepa d\\u00f3nde est\\u00e1 el repartidor):\\n\\nA) No tengo idea de c\\u00f3mo pasa eso.\\nB) He o\\u00eddo que existen "puentes" (llamados APIs), pero no s\\u00e9 c\\u00f3mo funcionan.\\nC) Entiendo que los sistemas se hablan entre s\\u00ed para darnos informaci\\u00f3n r\\u00e1pida.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  4: '*Pregunta 3 de 10* \\ud83d\\udee1\\ufe0f\\n\\nTe llega un correo "urgente" de tu banco o jefe pidiendo tu contrase\\u00f1a, \\u00bfqu\\u00e9 haces?\\n\\nA) Entro al link y la pongo r\\u00e1pido para no tener problemas.\\nB) Sospecho un poco, pero si el correo se ve real, termino entrando.\\nC) \\u00a1Alerta! S\\u00e9 que es un enga\\u00f1o (Phishing) y lo borro de inmediato.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  5: '*Pregunta 4 de 10* \\ud83d\\udee1\\ufe0f\\n\\n\\u00bfQu\\u00e9 es para ti la "Verificaci\\u00f3n en dos pasos" (el c\\u00f3digo extra que llega al cel)?\\n\\nA) Algo muy molesto que me quita tiempo para entrar a mis cuentas.\\nB) Lo tengo en algunas cosas, pero no entiendo bien para qu\\u00e9 sirve.\\nC) Mi seguro de vida digital; es la barrera que evita que me roben mi identidad.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  6: '*Pregunta 5 de 10* \\ud83e\\udd16\\n\\nSobre la Inteligencia Artificial (como ChatGPT), t\\u00fa piensas que:\\n\\nA) Es cosa de pel\\u00edculas o algo que solo los ingenieros usan.\\nB) Es para que los estudiantes hagan trampa en sus tareas.\\nC) Es mi asistente personal para redactar correos, planear y ahorrarme horas.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  7: '*Pregunta 6 de 10* \\ud83e\\udd16\\n\\nSi tienes que hacer una tarea dif\\u00edcil o un reporte largo:\\n\\nA) Me resigno a pasar horas haci\\u00e9ndolo a mano como siempre.\\nB) Busco en Google ejemplos para copiar y pegar un poco.\\nC) Uso Inteligencia Artificial para que me ayude con ideas y estructura.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  8: '*Pregunta 7 de 10* \\u26a1\\n\\nEl mundo hoy cambia muy r\\u00e1pido. Si en tu trabajo te cambian las reglas hoy:\\n\\nA) Me estreso y me cuesta mucho soltar mi forma anterior de trabajar.\\nB) Me adapto, pero me siento perdido y con mucho miedo a equivocarme.\\nC) Entiendo que el cambio es normal y busco r\\u00e1pido c\\u00f3mo aprender lo nuevo.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  9: '*Pregunta 8 de 10* \\u26a1\\n\\n\\u00bfSabes qu\\u00e9 es trabajar en un "Sprint" o usar un tablero de tareas (Kanban)?\\n\\nA) No, yo prefiero mi lista en papel o confiar en mi memoria.\\nB) He visto los tableros con etiquetas de colores, pero no s\\u00e9 usarlos.\\nC) S\\u00ed, me sirven para ver qu\\u00e9 est\\u00e1 pendiente, qu\\u00e9 va en proceso y qu\\u00e9 ya termin\\u00e9.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  10: '*Pregunta 9 de 10* \\ud83e\\udde0\\n\\nSi encuentras un error en el sistema de la empresa que te deja ver datos de otros:\\n\\nA) No digo nada, no es mi problema.\\nB) Me da curiosidad y reviso un poco antes de avisar.\\nC) Aviso de inmediato porque entiendo que la privacidad es sagrada.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  11: '*Pregunta 10 de 10* \\ud83e\\udde0\\n\\n\\u00bfC\\u00f3mo ves tu futuro profesional con tanta tecnolog\\u00eda?\\n\\nA) Tengo miedo de que las m\\u00e1quinas me quiten mi trabajo.\\nB) Creo que nada va a cambiar y seguir\\u00e9 trabajando igual que siempre.\\nC) S\\u00e9 que si aprendo a usar estas herramientas, tendr\\u00e9 mejores puestos y sueldos.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*'
};
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
        print('  Fixed: AT.PQ.10 Build Next Question (steps 2-11)')

    # Fix error build: QUESTIONS map step 2-11
    if nid == 'at-pq-err-build':
        params['jsCode'] = """const QUESTIONS = {
  2: '*Pregunta 1 de 10* \\ud83c\\udf10\\n\\nSi te piden trabajar en un archivo con un compa\\u00f1ero al mismo tiempo, t\\u00fa:\\n\\nA) Me confundo. Prefiero hacerlo yo solo y mandarlo luego por correo.\\nB) S\\u00e9 que se puede por internet, pero me da miedo que alguien borre mi parte.\\nC) \\u00a1Me encanta! Uso herramientas en la "Nube" para que avancemos juntos en vivo.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  3: '*Pregunta 2 de 10* \\ud83c\\udf10\\n\\n\\u00bfSabes c\\u00f3mo se conectan dos aplicaciones? (Ejemplo: que tu app de comida sepa d\\u00f3nde est\\u00e1 el repartidor):\\n\\nA) No tengo idea de c\\u00f3mo pasa eso.\\nB) He o\\u00eddo que existen "puentes" (llamados APIs), pero no s\\u00e9 c\\u00f3mo funcionan.\\nC) Entiendo que los sistemas se hablan entre s\\u00ed para darnos informaci\\u00f3n r\\u00e1pida.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  4: '*Pregunta 3 de 10* \\ud83d\\udee1\\ufe0f\\n\\nTe llega un correo "urgente" de tu banco o jefe pidiendo tu contrase\\u00f1a, \\u00bfqu\\u00e9 haces?\\n\\nA) Entro al link y la pongo r\\u00e1pido para no tener problemas.\\nB) Sospecho un poco, pero si el correo se ve real, termino entrando.\\nC) \\u00a1Alerta! S\\u00e9 que es un enga\\u00f1o (Phishing) y lo borro de inmediato.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  5: '*Pregunta 4 de 10* \\ud83d\\udee1\\ufe0f\\n\\n\\u00bfQu\\u00e9 es para ti la "Verificaci\\u00f3n en dos pasos" (el c\\u00f3digo extra que llega al cel)?\\n\\nA) Algo muy molesto que me quita tiempo para entrar a mis cuentas.\\nB) Lo tengo en algunas cosas, pero no entiendo bien para qu\\u00e9 sirve.\\nC) Mi seguro de vida digital; es la barrera que evita que me roben mi identidad.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  6: '*Pregunta 5 de 10* \\ud83e\\udd16\\n\\nSobre la Inteligencia Artificial (como ChatGPT), t\\u00fa piensas que:\\n\\nA) Es cosa de pel\\u00edculas o algo que solo los ingenieros usan.\\nB) Es para que los estudiantes hagan trampa en sus tareas.\\nC) Es mi asistente personal para redactar correos, planear y ahorrarme horas.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  7: '*Pregunta 6 de 10* \\ud83e\\udd16\\n\\nSi tienes que hacer una tarea dif\\u00edcil o un reporte largo:\\n\\nA) Me resigno a pasar horas haci\\u00e9ndolo a mano como siempre.\\nB) Busco en Google ejemplos para copiar y pegar un poco.\\nC) Uso Inteligencia Artificial para que me ayude con ideas y estructura.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  8: '*Pregunta 7 de 10* \\u26a1\\n\\nEl mundo hoy cambia muy r\\u00e1pido. Si en tu trabajo te cambian las reglas hoy:\\n\\nA) Me estreso y me cuesta mucho soltar mi forma anterior de trabajar.\\nB) Me adapto, pero me siento perdido y con mucho miedo a equivocarme.\\nC) Entiendo que el cambio es normal y busco r\\u00e1pido c\\u00f3mo aprender lo nuevo.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  9: '*Pregunta 8 de 10* \\u26a1\\n\\n\\u00bfSabes qu\\u00e9 es trabajar en un "Sprint" o usar un tablero de tareas (Kanban)?\\n\\nA) No, yo prefiero mi lista en papel o confiar en mi memoria.\\nB) He visto los tableros con etiquetas de colores, pero no s\\u00e9 usarlos.\\nC) S\\u00ed, me sirven para ver qu\\u00e9 est\\u00e1 pendiente, qu\\u00e9 va en proceso y qu\\u00e9 ya termin\\u00e9.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  10: '*Pregunta 9 de 10* \\ud83e\\udde0\\n\\nSi encuentras un error en el sistema de la empresa que te deja ver datos de otros:\\n\\nA) No digo nada, no es mi problema.\\nB) Me da curiosidad y reviso un poco antes de avisar.\\nC) Aviso de inmediato porque entiendo que la privacidad es sagrada.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*',
  11: '*Pregunta 10 de 10* \\ud83e\\udde0\\n\\n\\u00bfC\\u00f3mo ves tu futuro profesional con tanta tecnolog\\u00eda?\\n\\nA) Tengo miedo de que las m\\u00e1quinas me quiten mi trabajo.\\nB) Creo que nada va a cambiar y seguir\\u00e9 trabajando igual que siempre.\\nC) S\\u00e9 que si aprendo a usar estas herramientas, tendr\\u00e9 mejores puestos y sueldos.\\n\\n\\u2192 Responde con la letra: *A*, *B* o *C*'
};
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
        print('  Fixed: AT.PQ.E1 Build Error (steps 2-11)')

# Update workflow
print("\nUpdating AT Process Question...")
allowed_settings = {'executionOrder', 'callerPolicy'}
settings = {k: v for k, v in wf.get('settings', {}).items() if k in allowed_settings}

payload = {'name': wf['name'], 'nodes': wf['nodes'], 'connections': wf['connections'], 'settings': settings}

# Deactivate first
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}/deactivate'
req = urllib.request.Request(url, method='POST', data=b'')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
req.add_header('Content-Type', 'application/json')
urllib.request.urlopen(req, context=ctx, timeout=30)

url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}'
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, method='PUT')
req.add_header('Content-Type', 'application/json')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
try:
    resp = urllib.request.urlopen(req, context=ctx, timeout=60)
    result = json.loads(resp.read().decode())
    print(f"  Updated! version: {result.get('versionId')}")
except urllib.error.HTTPError as e:
    print(f"  ERROR {e.code}: {e.read().decode()[:500]}")

# Reactivate
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}/activate'
req = urllib.request.Request(url, method='POST', data=b'')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
req.add_header('Content-Type', 'application/json')
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
result = json.loads(resp.read().decode())
print(f"  Active: {result.get('active')}")
