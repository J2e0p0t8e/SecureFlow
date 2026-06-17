"""
Test rapide de l'API SecureFlow
Lance ce script pendant que le serveur tourne sur http://127.0.0.1:8000
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_home():
    """Test de la page d'accueil"""
    print("\n" + "="*80)
    print("TEST 1: Page d'accueil (GET /)")
    print("="*80)
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Page d'accueil accessible")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("⚠️  Assure-toi que le serveur tourne: python manage.py runserver")
        return False

def test_analyze_simple():
    """Test de l'endpoint /api/analyze/ avec du code simple"""
    print("\n" + "="*80)
    print("TEST 2: Analyse simple (POST /api/analyze/)")
    print("="*80)
    
    payload = {
        "mode": "A",
        "input_type": "text",
        "content": "print('Hello World')",
        "label": "Test Simple"
    }
    
    try:
        print(f"Envoi de la requête à {BASE_URL}/api/analyze/")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/api/analyze/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes timeout
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Analyse réussie!")
            print(f"\nMode: {data.get('mode')}")
            print(f"Room ID: {data.get('room_id')}")
            print(f"Session ID: {data.get('session_id')}")
            print(f"Audit ID: {data.get('audit_id')}")
            print(f"Décision: {data.get('decision')}")
            print(f"Nombre d'agents: {len(data.get('agents', []))}")
            
            # Afficher les agents
            print("\n--- Agents ---")
            for agent in data.get('agents', []):
                print(f"- {agent['name']}")
            
            return data.get('session_id')
        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - L'analyse prend trop de temps (>2 min)")
        print("⚠️  Cela peut être normal pour la première requête (agents Band)")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_pdf_download(session_id):
    """Test du téléchargement PDF"""
    if not session_id:
        print("\n⚠️  Pas de session_id, skip du test PDF")
        return False
    
    print("\n" + "="*80)
    print(f"TEST 3: Téléchargement PDF (GET /api/pdf/{session_id}/)")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/pdf/{session_id}/")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Sauvegarder le PDF
            filename = f"test-rapport-{session_id[:8]}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ PDF téléchargé: {filename}")
            print(f"Taille: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_invalid_mode():
    """Test avec un mode invalide"""
    print("\n" + "="*80)
    print("TEST 4: Mode invalide (devrait retourner 400)")
    print("="*80)
    
    payload = {
        "mode": "Z",
        "input_type": "text",
        "content": "test"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Erreur correctement gérée")
            data = response.json()
            print(f"Message: {data.get('error')}")
            return True
        else:
            print(f"❌ Status inattendu: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 TESTS RAPIDES API SECUREFLOW")
    print("="*80)
    print("⚠️  Assure-toi que le serveur tourne:")
    print("    python manage.py runserver")
    print("="*80)
    
    results = []
    
    # Test 1: Page d'accueil
    results.append(("Page d'accueil", test_home()))
    
    # Test 2: Analyse simple
    session_id = test_analyze_simple()
    results.append(("Analyse Mode A", session_id is not None))
    
    # Test 3: PDF (si analyse réussie)
    if session_id:
        results.append(("Téléchargement PDF", test_pdf_download(session_id)))
    
    # Test 4: Validation erreurs
    results.append(("Validation erreurs", test_invalid_mode()))
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ DES TESTS")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés! L'API fonctionne correctement.")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifie les logs du serveur.")

# Made with Bob
