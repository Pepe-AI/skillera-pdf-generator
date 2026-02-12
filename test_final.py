import requests
import json
import time

# Configuración
WEBHOOK_URL = "https://n8n-nqt7.onrender.com/webhook/kommo-whatsapp-test"

# Payload de prueba
payload = {
    "account_id": "123456",
    "messages": {
        "add": [
            {
                "id": int(time.time()),
                "entity_id": 12345,
                "entity_type": "lead",
                "text": "Hola, esta es una prueba definitiva",
                "origin": "whatsapp",
                "created_at": int(time.time()),
                "author_id": 999,
                "attachments": []
            }
        ]
    },
    "leads": {
        "add": [
            {
                "id": 12345,
                "name": "Test Contact"
            }
        ]
    }
}

print("="*60)
print("PRUEBA DEFINITIVA DEL WEBHOOK")
print("="*60)
print(f"\n📍 URL: {WEBHOOK_URL}")
print(f"📦 Payload:\n{json.dumps(payload, indent=2)}\n")
print("Enviando petición...\n")

try:
    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Test-Script/1.0"
        },
        timeout=30
    )
    
    print("="*60)
    print("RESPUESTA DEL SERVIDOR")
    print("="*60)
    print(f"✓ Status Code: {response.status_code}")
    print(f"✓ Headers: {dict(response.headers)}")
    print(f"✓ Body: {response.text}\n")
    
    if response.status_code == 200:
        print("="*60)
        print("✅ ¡ÉXITO!")
        print("="*60)
        print("El webhook se ejecutó correctamente.")
        print("Ve a n8n → Executions para ver los detalles.\n")
        
        # Intentar parsear la respuesta
        try:
            data = response.json()
            print(f"Datos de respuesta: {json.dumps(data, indent=2)}")
        except:
            pass
    elif response.status_code == 404:
        print("="*60)
        print("❌ ERROR 404: Webhook No Encontrado")
        print("="*60)
        print("El workflow NO está activo o la URL es incorrecta.")
        print("Verifica que el workflow esté ACTIVO (toggle verde).\n")
    elif response.status_code == 500:
        print("="*60)
        print("❌ ERROR 500: Error Interno del Servidor")
        print("="*60)
        print("Hay un error en la ejecución del workflow.")
        print("Ve a n8n → Executions para ver el error específico.\n")
    else:
        print("="*60)
        print(f"⚠️ Respuesta Inesperada: {response.status_code}")
        print("="*60)
        
except requests.exceptions.Timeout:
    print("="*60)
    print("❌ TIMEOUT")
    print("="*60)
    print("El webhook tardó más de 30 segundos en responder.")
    print("Esto puede indicar un bucle infinito o proceso muy lento.\n")
    
except requests.exceptions.ConnectionError:
    print("="*60)
    print("❌ ERROR DE CONEXIÓN")
    print("="*60)
    print("No se pudo conectar al servidor n8n.")
    print("Verifica que la URL sea correcta y el servidor esté activo.\n")
    
except Exception as e:
    print("="*60)
    print("❌ ERROR INESPERADO")
    print("="*60)
    print(f"Error: {str(e)}\n")

print("="*60)
print("FIN DE LA PRUEBA")
print("="*60)