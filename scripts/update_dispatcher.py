"""Update Dispatcher workflow to add AT route."""
import json, urllib.request, ssl

N8N_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMDYyOGNmYi04MGYxLTQwMjUtYmE1MC02ZDJkZWZjNmY4ZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiN2MxMTM5ZTYtNzQ2OS00ZTAwLThkODMtZDRkODcyNjEwNzNhIiwiaWF0IjoxNzcyNjAyOTk5fQ.XbXiBQztJgmH07BPqlO1HCX2iGpm6klvVpQ378WozKM'
ctx = ssl.create_default_context()
CHATBOT_AT_WF = '2KhIR3MCBotra5qe'
REDIS_CREDS = {"redis": {"id": "zp9CDC6PvjpPyYLX", "name": "redis render"}}

# Get latest version
url = 'https://n8n-nqt7.onrender.com/api/v1/workflows/Exd9sqOZ03HIvYAI'
req = urllib.request.Request(url)
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
wf = json.loads(resp.read().decode())
print(f'Got Dispatcher: {len(wf["nodes"])} nodes, version={wf["versionId"]}')

# 1. Add AT rule to Switch "2.1 Route by test_type"
for node in wf['nodes']:
    if node['id'] == 'route-test-type':
        rules = node['parameters']['rules']['values']
        rules.append({
            'conditions': {
                'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'strict', 'version': 2},
                'conditions': [{
                    'id': 'route-at',
                    'leftValue': "={{ $('1.6 Handle Empty').item.json.test_type }}",
                    'operator': {'type': 'string', 'operation': 'equals'},
                    'rightValue': 'at'
                }],
                'combinator': 'and'
            }
        })
        print(f'  Switch route-test-type: now has {len(rules)} rules')
        break

# 2. Add node "4.5 Call Chatbot AT (sesion)"
# Clone pattern from "4.2 Call Chatbot IE (sesion)"
ie_node = None
for node in wf['nodes']:
    if node['id'] == 'call-ie-existing':
        ie_node = node
        break

at_call_node = {
    'id': 'call-at-existing',
    'name': '4.5 Call Chatbot AT (sesion)',
    'type': 'n8n-nodes-base.executeWorkflow',
    'typeVersion': 1.2,
    'position': [3680, 740],
    'parameters': {
        'workflowId': {'__rl': True, 'value': CHATBOT_AT_WF, 'mode': 'id'},
        'workflowInputs': {
            'mappingMode': 'defineBelow',
            'value': {
                'message_text': "={{ $('1.6 Handle Empty').item.json.message_text }}",
                'contact_id': "={{ $('1.6 Handle Empty').item.json.contact_id }}",
                'entity_id': "={{ $('1.6 Handle Empty').item.json.entity_id }}",
                'chat_id': "={{ $('1.6 Handle Empty').item.json.chat_id }}",
                'author_name': "={{ $('1.6 Handle Empty').item.json.author_name }}",
                'lead_id': "={{ $('1.6 Handle Empty').item.json.lead_id }}",
                'kommo_field_id': "={{ $('1.6 Handle Empty').item.json.kommo_field_id }}",
                'kommo_token': "={{ $('1.6 Handle Empty').item.json.kommo_token }}",
                'kommo_dominio': "={{ $('1.6 Handle Empty').item.json.kommo_dominio }}"
            },
            'matchingColumns': [],
            'schema': [
                {'id': f, 'displayName': f, 'required': False, 'defaultMatch': False,
                 'display': True, 'canBeUsedToMatch': True, 'type': 'string', 'removed': False}
                for f in ['message_text', 'contact_id', 'entity_id', 'chat_id',
                          'author_name', 'lead_id', 'kommo_field_id', 'kommo_token', 'kommo_dominio']
            ],
            'attemptToConvertTypes': False,
            'convertFieldsToString': True
        },
        'options': {}
    }
}
wf['nodes'].append(at_call_node)
print('  Node added: 4.5 Call Chatbot AT (sesion)')

# 3. Add node "5.5 Redis DEL lock (AT sesion)"
redis_del_node = {
    'id': 'redis-lock-del-at',
    'name': '5.5 Redis DEL lock (AT sesion)',
    'type': 'n8n-nodes-base.redis',
    'typeVersion': 1,
    'position': [3920, 740],
    'parameters': {
        'operation': 'delete',
        'key': "=lock:{{ $('1.4 Parsear Mensaje').item.json.contact_id }}"
    },
    'credentials': REDIS_CREDS
}
wf['nodes'].append(redis_del_node)
print('  Node added: 5.5 Redis DEL lock (AT sesion)')

# 4. Add connections
conns = wf['connections']

# Switch output 2 -> 4.5 Call Chatbot AT
switch_name = '2.1 Route by test_type'
if switch_name in conns:
    main = conns[switch_name]['main']
    main.append([{'node': '4.5 Call Chatbot AT (sesion)', 'type': 'main', 'index': 0}])
    print(f'  Connection: Switch output[2] -> 4.5 Call Chatbot AT')

# 4.5 -> 5.5
conns['4.5 Call Chatbot AT (sesion)'] = {
    'main': [[{'node': '5.5 Redis DEL lock (AT sesion)', 'type': 'main', 'index': 0}]]
}
print('  Connection: 4.5 -> 5.5 Redis DEL lock')

# 5. PUT update
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

url = 'https://n8n-nqt7.onrender.com/api/v1/workflows/Exd9sqOZ03HIvYAI'
data = json.dumps(update_payload).encode('utf-8')
req = urllib.request.Request(url, data=data, method='PUT')
req.add_header('Content-Type', 'application/json')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)

try:
    resp = urllib.request.urlopen(req, context=ctx, timeout=60)
    result = json.loads(resp.read().decode())
    print(f'\nSUCCESS! Dispatcher updated.')
    print(f'  versionId: {result.get("versionId")}')
    print(f'  Nodes: {len(result.get("nodes", []))}')
    print(f'  Active: {result.get("active")}')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'\nERROR {e.code}: {body[:500]}')
