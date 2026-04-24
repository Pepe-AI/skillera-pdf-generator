"""Update Agent Commands workflow to add AT route."""
import json, urllib.request, ssl

N8N_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMDYyOGNmYi04MGYxLTQwMjUtYmE1MC02ZDJkZWZjNmY4ZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiN2MxMTM5ZTYtNzQ2OS00ZTAwLThkODMtZDRkODcyNjEwNzNhIiwiaWF0IjoxNzcyNjAyOTk5fQ.XbXiBQztJgmH07BPqlO1HCX2iGpm6klvVpQ378WozKM'
ctx = ssl.create_default_context()
CHATBOT_AT_WF = '2KhIR3MCBotra5qe'

# Get latest version
url = 'https://n8n-nqt7.onrender.com/api/v1/workflows/qFfuyTKvrPCr8lov'
req = urllib.request.Request(url)
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
wf = json.loads(resp.read().decode())
print(f'Got Agent Commands: {len(wf["nodes"])} nodes, version={wf["versionId"]}')

# 1. Update ext-lead jsCode to add 'at' detection
for node in wf['nodes']:
    if node['id'] == 'ext-lead':
        old_code = node['parameters']['jsCode']
        old_block = "let command = 'liderazgo';\nif (msgN.includes('ie') || msgN.includes('emocional')) command = 'ie';\nelse if (msgN.includes('liderazgo') || msgN.includes('lider')) command = 'liderazgo';"
        new_block = "let command = 'liderazgo';\nif (msgN.includes('ie') || msgN.includes('emocional')) command = 'ie';\nelse if (msgN.includes('at') || msgN.includes('alfabetizacion') || msgN.includes('tecnologica')) command = 'at';\nelse if (msgN.includes('liderazgo') || msgN.includes('lider')) command = 'liderazgo';"
        if old_block in old_code:
            node['parameters']['jsCode'] = old_code.replace(old_block, new_block)
            print('  ext-lead: AT detection added')
        else:
            print('  WARNING: block not found in ext-lead')

        old_msg = "const message_text = command === 'ie' ? 'diagnostico' : 'liderazgo';"
        new_msg = "const message_text = command === 'ie' ? 'diagnostico' : command === 'at' ? 'at' : 'liderazgo';"
        if old_msg in node['parameters']['jsCode']:
            node['parameters']['jsCode'] = node['parameters']['jsCode'].replace(old_msg, new_msg)
            print('  ext-lead: message_text updated')
        break

# 2. Add AT rule to Switch route-cmd
for node in wf['nodes']:
    if node['id'] == 'route-cmd':
        rules = node['parameters']['rules']['values']
        rules.append({
            'conditions': {
                'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'strict', 'version': 2},
                'conditions': [{
                    'id': 'cmd-at',
                    'leftValue': "={{ $('2.2 Extraer Lead y Comando').item.json.command }}",
                    'operator': {'operation': 'equals', 'type': 'string'},
                    'rightValue': 'at'
                }],
                'combinator': 'and'
            }
        })
        print(f'  Switch: now has {len(rules)} rules')
        break

# 3. Add new node
new_node = {
    'id': 'call-at',
    'name': '3.5 Call Chatbot AT (directo)',
    'type': 'n8n-nodes-base.executeWorkflow',
    'typeVersion': 1.2,
    'position': [1120, 592],
    'notes': 'Llama al Chatbot AT directamente.',
    'parameters': {
        'workflowId': {'__rl': True, 'mode': 'id', 'value': CHATBOT_AT_WF},
        'workflowInputs': {
            'attemptToConvertTypes': False,
            'convertFieldsToString': True,
            'mappingMode': 'defineBelow',
            'matchingColumns': [],
            'schema': [
                {'canBeUsedToMatch': True, 'defaultMatch': False, 'display': True,
                 'displayName': f, 'id': f, 'removed': False, 'required': False, 'type': 'string'}
                for f in ['message_text', 'contact_id', 'entity_id', 'lead_id',
                          'kommo_field_id', 'kommo_token', 'kommo_dominio']
            ],
            'value': {
                'contact_id': "={{ $('2.2 Extraer Lead y Comando').item.json.contact_id }}",
                'entity_id': "={{ $('2.2 Extraer Lead y Comando').item.json.lead_id }}",
                'kommo_dominio': "={{ $('2.2 Extraer Lead y Comando').item.json.kommo_dominio }}",
                'kommo_field_id': "={{ $('2.2 Extraer Lead y Comando').item.json.field_mensaje_ia }}",
                'kommo_token': "={{ $('2.2 Extraer Lead y Comando').item.json.kommo_token }}",
                'lead_id': "={{ $('2.2 Extraer Lead y Comando').item.json.lead_id }}",
                'message_text': "={{ $('2.2 Extraer Lead y Comando').item.json.message_text }}"
            }
        },
        'options': {}
    }
}
wf['nodes'].append(new_node)
print('  Node added: 3.5 Call Chatbot AT (directo)')

# 4. Add connection Switch output 2 -> new node
switch_name = '2.4 Route by Command'
if switch_name in wf['connections']:
    main = wf['connections'][switch_name]['main']
    main.append([{'index': 0, 'node': '3.5 Call Chatbot AT (directo)', 'type': 'main'}])
    print(f'  Connection: Switch output[2] -> 3.5 Call Chatbot AT')

# 5. PUT update
# Only include allowed settings keys
allowed_settings = {'executionOrder', 'callerPolicy', 'saveDataErrorExecution',
                    'saveDataSuccessExecution', 'saveExecutionProgress',
                    'saveManualExecutions', 'executionTimeout', 'timezone', 'errorWorkflow'}
settings = {k: v for k, v in wf.get('settings', {}).items() if k in allowed_settings}

update_payload = {
    'name': wf['name'],
    'nodes': wf['nodes'],
    'connections': wf['connections'],
    'settings': settings
}

url = 'https://n8n-nqt7.onrender.com/api/v1/workflows/qFfuyTKvrPCr8lov'
data = json.dumps(update_payload).encode('utf-8')
req = urllib.request.Request(url, data=data, method='PUT')
req.add_header('Content-Type', 'application/json')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)

try:
    resp = urllib.request.urlopen(req, context=ctx, timeout=60)
    result = json.loads(resp.read().decode())
    print(f'\nSUCCESS! Agent Commands updated.')
    print(f'  versionId: {result.get("versionId")}')
    print(f'  Nodes: {len(result.get("nodes", []))}')
    print(f'  Active: {result.get("active")}')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'\nERROR {e.code}: {body[:500]}')
