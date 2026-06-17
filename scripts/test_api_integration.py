"""
Script de test pour vérifier l'intégration de l'API avec l'orchestrateur.
Teste l'endpoint /api/analyze/ avec le Mode A.
"""

import json
import sys
import os

# Ajouter le répertoire parent au path pour les imports Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secureflow.settings')

import django
django.setup()

from django.test import RequestFactory
from apps.api.views import analyze


def test_mode_a_with_text():
    """Test Mode A avec du texte simple"""
    print("=" * 80)
    print("TEST 1: Mode A avec input_type=text")
    print("=" * 80)
    
    factory = RequestFactory()
    
    # Code vulnérable simple pour tester
    test_code = """
import sqlite3

def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Vulnérabilité SQL Injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()
"""
    
    request_data = {
        "mode": "A",
        "input_type": "text",
        "content": test_code,
        "label": "Test SQL Injection"
    }
    
    request = factory.post(
        '/api/analyze/',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    try:
        response = analyze(request)
        result = json.loads(response.content)
        
        print("\n✅ Réponse reçue avec succès!")
        print(f"\nMode: {result.get('mode')}")
        print(f"Room ID: {result.get('room_id')}")
        print(f"Audit ID: {result.get('audit_id')}")
        print(f"Décision: {result.get('decision')}")
        print(f"\nNombre d'agents: {len(result.get('agents', []))}")
        
        print("\n--- Résultats des agents ---")
        for agent in result.get('agents', []):
            print(f"\n{agent['name']}:")
            print(agent['content'][:200] + "..." if len(agent['content']) > 200 else agent['content'])
        
        print("\n--- Rapport final (extrait) ---")
        final_report = result.get('final_report', '')
        print(final_report[:500] + "..." if len(final_report) > 500 else final_report)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_mode():
    """Test avec un mode invalide"""
    print("\n" + "=" * 80)
    print("TEST 2: Mode invalide (devrait retourner une erreur)")
    print("=" * 80)
    
    factory = RequestFactory()
    
    request_data = {
        "mode": "Z",
        "input_type": "text",
        "content": "print('test')"
    }
    
    request = factory.post(
        '/api/analyze/',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    try:
        response = analyze(request)
        result = json.loads(response.content)
        
        if response.status_code == 400 and 'error' in result:
            print(f"\n✅ Erreur correctement gérée: {result['error']}")
            return True
        else:
            print(f"\n❌ Réponse inattendue: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        return False


def test_mode_b_not_implemented():
    """Test Mode B (devrait retourner 501 Not Implemented)"""
    print("\n" + "=" * 80)
    print("TEST 3: Mode B (pas encore implémenté)")
    print("=" * 80)
    
    factory = RequestFactory()
    
    request_data = {
        "mode": "B",
        "input_type": "text",
        "content": "print('test')"
    }
    
    request = factory.post(
        '/api/analyze/',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    try:
        response = analyze(request)
        result = json.loads(response.content)
        
        if response.status_code == 501 and 'error' in result:
            print(f"\n✅ Mode B correctement marqué comme non implémenté: {result['message']}")
            return True
        else:
            print(f"\n❌ Réponse inattendue: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🚀 TESTS D'INTÉGRATION API - PERSONNE 5\n")
    
    results = []
    
    # Test 1: Mode A fonctionnel
    results.append(("Mode A avec texte", test_mode_a_with_text()))
    
    # Test 2: Validation des erreurs
    results.append(("Mode invalide", test_invalid_mode()))
    
    # Test 3: Modes non implémentés
    results.append(("Mode B non implémenté", test_mode_b_not_implemented()))
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés! L'intégration fonctionne correctement.")
        sys.exit(0)
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez la configuration.")
        sys.exit(1)

# Made with Bob
