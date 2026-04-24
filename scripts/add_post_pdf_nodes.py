"""
Add post-PDF nodes H.1-H.5 to AT Process Question workflow.
Chain after AT.PQ.10e Call Calculate AT Scores.
"""
import json, urllib.request, ssl

N8N_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMDYyOGNmYi04MGYxLTQwMjUtYmE1MC02ZDJkZWZjNmY4ZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiN2MxMTM5ZTYtNzQ2OS00ZTAwLThkODMtZDRkODcyNjEwNzNhIiwiaWF0IjoxNzcyNjAyOTk5fQ.XbXiBQztJgmH07BPqlO1HCX2iGpm6klvVpQ378WozKM'
ctx = ssl.create_default_context()
WF_ID = '8cv7GiAK6nIOLpXM'
SEND_FILE_WF = 'uuAzYnZJtzpxVNd3'
SESSIONS_TABLE = 'tBaZMEOVw2tvcswf'
AT_RESPONSES_TABLE = 'B4pPUen5ysuETffw'
BOT_ID = 64784

# Get current workflow
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}'
req = urllib.request.Request(url)
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
wf = json.loads(resp.read().decode())
print(f'Got AT Process Question: {len(wf["nodes"])} nodes')

def sf(name, ftype="string"):
    return {"id": name, "displayName": name, "required": False, "defaultMatch": False,
            "display": True, "canBeUsedToMatch": True, "type": ftype, "removed": False}

# ── H.1: HTTP Request: Generate PDF ──
h1_node = {
    "id": "at-pq-gen-pdf",
    "name": "H.1 Generate AT PDF",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [2096, 176],
    "continueOnFail": True,
    "parameters": {
        "method": "POST",
        "url": "={{ $vars.PDF_GENERATOR_URL }}/generate-at-pdf-base64",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "content-type", "value": "application/json"},
            {"name": "accept", "value": "application/json"}
        ]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ user: { name: $json.name || 'Sin nombre' }, results: { total_score: $json.total_score, nivel: $json.nivel } }) }}",
        "options": {
            "timeout": 60000,
            "retry": {"count": 2, "intervalMs": 5000}
        }
    }
}
wf['nodes'].append(h1_node)
print('  Added: H.1 Generate AT PDF')

# ── H.2: Send File via Kommo Chat ──
h2_node = {
    "id": "at-pq-send-file",
    "name": "H.2 Send PDF via WhatsApp",
    "type": "n8n-nodes-base.executeWorkflow",
    "typeVersion": 1.2,
    "position": [2336, 176],
    "parameters": {
        "workflowId": {"__rl": True, "value": SEND_FILE_WF, "mode": "id"},
        "workflowInputs": {
            "mappingMode": "defineBelow",
            "value": {
                "pdf_base64": "={{ $json.pdf_base64 }}",
                "filename": "={{ $json.filename }}",
                "contact_id": "={{ $('AT.PQ.10d Prep Scores Payload').first().json.contact_id }}",
                "entity_id": "={{ $('AT.PQ.10d Prep Scores Payload').first().json.entity_id }}",
                "kommo_token": "={{ $('AT.PQ.10d Prep Scores Payload').first().json.kommo_token }}",
                "kommo_dominio": "={{ $('AT.PQ.10d Prep Scores Payload').first().json.kommo_dominio }}"
            },
            "matchingColumns": [],
            "schema": [sf(f) for f in ["pdf_base64", "filename", "contact_id", "entity_id", "kommo_token", "kommo_dominio"]],
            "attemptToConvertTypes": False,
            "convertFieldsToString": True
        },
        "options": {}
    }
}
wf['nodes'].append(h2_node)
print('  Added: H.2 Send PDF via WhatsApp')

# ── H.3: Completion message ──
# Build message code
h3_build = {
    "id": "at-pq-build-done",
    "name": "H.3 Build Done Message",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [2576, 176],
    "parameters": {
        "jsCode": "const src = $('AT.PQ.10d Prep Scores Payload').first().json;\nconst msgText = 'Tu diagnostico esta listo. Revisalo arriba.';\nconst patchBody = { custom_fields_values: [{ field_id: parseInt(src.kommo_field_id), values: [{ value: msgText }] }] };\nreturn [{ json: { patch_body_string: JSON.stringify(patchBody), contact_id: src.contact_id, entity_id: src.entity_id, lead_id: src.lead_id, kommo_field_id: src.kommo_field_id, kommo_token: src.kommo_token, kommo_dominio: src.kommo_dominio } }];"
    }
}
wf['nodes'].append(h3_build)

h3_patch = {
    "id": "at-pq-done-patch",
    "name": "H.3a PATCH Done",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [2816, 176],
    "continueOnFail": True,
    "parameters": {
        "method": "PATCH",
        "url": "={{ $json.kommo_dominio }}/api/v4/leads/{{ $json.lead_id }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": "=Bearer {{ $json.kommo_token }}"},
            {"name": "content-type", "value": "application/json"}
        ]},
        "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
        "body": "={{ $json.patch_body_string }}", "options": {}
    }
}
wf['nodes'].append(h3_patch)

h3_sb = {
    "id": "at-pq-done-sb",
    "name": "H.3b Salesbot Done",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [3024, 176],
    "continueOnFail": True,
    "parameters": {
        "method": "POST",
        "url": "={{ $('H.3 Build Done Message').item.json.kommo_dominio }}/api/v2/salesbot/run",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": "=Bearer {{ $('H.3 Build Done Message').item.json.kommo_token }}"},
            {"name": "accept", "value": "application/json"}
        ]},
        "sendBody": True, "specifyBody": "json",
        "jsonBody": f'=[{{"bot_id": {BOT_ID}, "entity_id": {{{{ $(\'H.3 Build Done Message\').item.json.entity_id }}}}, "entity_type": "leads"}}]',
        "options": {}
    }
}
wf['nodes'].append(h3_sb)

h3_wait = {
    "id": "at-pq-done-wait",
    "name": "Wait 2s Done",
    "type": "n8n-nodes-base.wait",
    "typeVersion": 1.1,
    "position": [3232, 176],
    "parameters": {"amount": 2}
}
wf['nodes'].append(h3_wait)

h3_clear = {
    "id": "at-pq-done-clear",
    "name": "H.3c Clear Done",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [3424, 176],
    "continueOnFail": True,
    "parameters": {
        "method": "PATCH",
        "url": "={{ $('H.3 Build Done Message').item.json.kommo_dominio }}/api/v4/leads/{{ $('H.3 Build Done Message').item.json.lead_id }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": "=Bearer {{ $('H.3 Build Done Message').item.json.kommo_token }}"},
            {"name": "content-type", "value": "application/json"}
        ]},
        "sendBody": True,
        "bodyParameters": {"parameters": [
            {"name": "custom_fields_values",
             "value": "={{ [{field_id: parseInt($('H.3 Build Done Message').item.json.kommo_field_id), values: [{value: ''}]}] }}"}
        ]}, "options": {}
    }
}
wf['nodes'].append(h3_clear)
print('  Added: H.3 Done message chain (5 nodes)')

# ── H.4: PATCH tests_completados ──
h4_node = {
    "id": "at-pq-patch-tests",
    "name": "H.4 PATCH tests_completados",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [3664, 176],
    "continueOnFail": True,
    "parameters": {
        "method": "PATCH",
        "url": "={{ $('H.3 Build Done Message').item.json.kommo_dominio }}/api/v4/leads/{{ $('H.3 Build Done Message').item.json.lead_id }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "authorization", "value": "=Bearer {{ $('H.3 Build Done Message').item.json.kommo_token }}"},
            {"name": "content-type", "value": "application/json"}
        ]},
        "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
        "body": "={{ JSON.stringify({custom_fields_values: [{field_id: 2283634, values: [{value: true}]}]}) }}",
        "options": {}
    }
}
wf['nodes'].append(h4_node)
print('  Added: H.4 PATCH tests_completados')

# ── H.5: Cleanup (delete sessions + at_responses) ──
h5_sessions = {
    "id": "at-pq-del-sessions",
    "name": "H.5a DELETE Session",
    "type": "n8n-nodes-base.dataTable",
    "typeVersion": 1.1,
    "position": [3904, 96],
    "parameters": {
        "operation": "deleteById",
        "dataTableId": {"__rl": True, "value": SESSIONS_TABLE, "mode": "id"},
        "filters": {"conditions": [
            {"keyName": "phone_number", "keyValue": "={{ $('H.3 Build Done Message').item.json.contact_id }}"}
        ]}
    }
}
wf['nodes'].append(h5_sessions)

h5_responses = {
    "id": "at-pq-del-responses",
    "name": "H.5b DELETE AT Responses",
    "type": "n8n-nodes-base.dataTable",
    "typeVersion": 1.1,
    "position": [3904, 256],
    "parameters": {
        "operation": "deleteById",
        "dataTableId": {"__rl": True, "value": AT_RESPONSES_TABLE, "mode": "id"},
        "filters": {"conditions": [
            {"keyName": "phone_number", "keyValue": "={{ $('H.3 Build Done Message').item.json.contact_id }}"}
        ]}
    }
}
wf['nodes'].append(h5_responses)
print('  Added: H.5 Cleanup (2 DELETE nodes)')

# ── Add connections ──
conns = wf['connections']

# Chain: AT.PQ.10e -> H.1 -> H.2 -> H.3 Build -> H.3a PATCH -> H.3b Salesbot -> Wait -> H.3c Clear -> H.4 -> H.5a/H.5b
conns['AT.PQ.10e Call Calculate AT Scores'] = {"main": [[{"node": "H.1 Generate AT PDF", "type": "main", "index": 0}]]}
conns['H.1 Generate AT PDF'] = {"main": [[{"node": "H.2 Send PDF via WhatsApp", "type": "main", "index": 0}]]}
conns['H.2 Send PDF via WhatsApp'] = {"main": [[{"node": "H.3 Build Done Message", "type": "main", "index": 0}]]}
conns['H.3 Build Done Message'] = {"main": [[{"node": "H.3a PATCH Done", "type": "main", "index": 0}]]}
conns['H.3a PATCH Done'] = {"main": [[{"node": "H.3b Salesbot Done", "type": "main", "index": 0}]]}
conns['H.3b Salesbot Done'] = {"main": [[{"node": "Wait 2s Done", "type": "main", "index": 0}]]}
conns['Wait 2s Done'] = {"main": [[{"node": "H.3c Clear Done", "type": "main", "index": 0}]]}
conns['H.3c Clear Done'] = {"main": [[{"node": "H.4 PATCH tests_completados", "type": "main", "index": 0}]]}
# H.4 -> both H.5a and H.5b in parallel
conns['H.4 PATCH tests_completados'] = {"main": [[
    {"node": "H.5a DELETE Session", "type": "main", "index": 0},
    {"node": "H.5b DELETE AT Responses", "type": "main", "index": 0}
]]}
print('  Added all connections')

# ── Update workflow ──
print("\nUpdating AT Process Question with post-PDF nodes...")

# Deactivate
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}/deactivate'
req = urllib.request.Request(url, method='POST', data=b'')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
req.add_header('Content-Type', 'application/json')
urllib.request.urlopen(req, context=ctx, timeout=30)

allowed = {'executionOrder', 'callerPolicy'}
settings = {k: v for k, v in wf.get('settings', {}).items() if k in allowed}
payload = {'name': wf['name'], 'nodes': wf['nodes'], 'connections': wf['connections'], 'settings': settings}

url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}'
data = json.dumps(payload).encode('utf-8')
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
url = f'https://n8n-nqt7.onrender.com/api/v1/workflows/{WF_ID}/activate'
req = urllib.request.Request(url, method='POST', data=b'')
req.add_header('X-N8N-API-KEY', N8N_API_KEY)
req.add_header('Content-Type', 'application/json')
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
result = json.loads(resp.read().decode())
print(f"  Active: {result.get('active')}")

print("\nDone! Total nodes now in AT Process Question:", len(wf['nodes']))
