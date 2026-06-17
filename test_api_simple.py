"""
Test simple de l'API SecureFlow sans dépendances complexes
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secureflow.settings')
django.setup()

from django.test import RequestFactory
from apps.api.views import analyze
import json

def test_api():
    print("=" * 80)
    print("TEST API SECUREFLOW")
    print("=" * 80)
    
    # Créer une requête de test
    factory = RequestFactory()
    
    data = {
        "mode": "A",
        "input_type": "text",
        "content": "api_key = 'hardcoded-secret'",
        "label": "test-simple"
    }
    
    print("\n📤 Envoi de la requête:")
    print(json.dumps(data, indent=2))
    
    # Créer la requête POST
    request = factory.post(
        '/api/analyze/',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    print("\n⏳ Appel de l'API...")
    
    try:
        # Appeler la vue
        response = analyze(request)
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = json.loads(response.content.decode())
            print("\n📥 Réponse reçue:")
            print(f"  - Mode: {result.get('mode')}")
            print(f"  - Room ID: {result.get('room_id')}")
            print(f"  - Decision: {result.get('decision')}")
            print(f"  - Audit ID: {result.get('audit_id')}")
            print(f"  - Nombre d'agents: {len(result.get('agents', []))}")
            
            print("\n📋 Agents:")
            for agent in result.get('agents', []):
                print(f"  - {agent.get('name')}: {agent.get('content')[:50]}...")
            
            print("\n✅ TEST RÉUSSI !")
            return True
        else:
            print(f"\n❌ Erreur HTTP {response.status_code}")
            print(response.content.decode())
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)

# Made with Bob
