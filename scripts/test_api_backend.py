"""
Script de test pour l'API Backend (Personne 2).
Teste l'ingestion GitHub, ZIP et l'endpoint API.
"""

import sys
from pathlib import Path

# Ajouter le projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django
django.setup()


def test_github_ingestion():
    """Test de l'ingestion GitHub."""
    print("\n" + "="*80)
    print("TEST 1: Ingestion GitHub")
    print("="*80)
    
    from apps.ingestion.github import fetch_github_project, is_valid_github_url
    
    # Test validation URL
    test_urls = [
        ("https://github.com/user/repo", True),
        ("https://github.com/user/repo/tree/main", True),
        ("https://gitlab.com/user/repo", False),
        ("not-a-url", False),
    ]
    
    print("\n1.1 Validation d'URLs:")
    for url, expected in test_urls:
        result = is_valid_github_url(url)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {url}: {result}")
    
    # Test récupération d'un petit repo public
    print("\n1.2 Récupération d'un repo public (exemple):")
    print("  URL: https://github.com/octocat/Hello-World")
    
    try:
        content = fetch_github_project(
            "https://github.com/octocat/Hello-World",
            max_files=5
        )
        print(f"  ✓ Contenu récupéré: {len(content)} caractères")
        print(f"  Aperçu (200 premiers caractères):")
        print(f"  {content[:200]}...")
    except Exception as e:
        print(f"  ✗ Erreur: {e}")


def test_zip_ingestion():
    """Test de l'ingestion ZIP."""
    print("\n" + "="*80)
    print("TEST 2: Ingestion ZIP")
    print("="*80)
    
    from apps.ingestion.zip_loader import extract_zip_project, validate_zip_file
    import zipfile
    from io import BytesIO
    
    # Créer un ZIP de test en mémoire
    print("\n2.1 Création d'un ZIP de test:")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test.py", "print('Hello from ZIP')\n")
        zf.writestr("README.md", "# Test Project\n")
        zf.writestr("node_modules/lib.js", "// Should be ignored\n")
    
    zip_bytes = zip_buffer.getvalue()
    print(f"  ✓ ZIP créé: {len(zip_bytes)} bytes")
    
    # Test validation
    print("\n2.2 Validation du ZIP:")
    is_valid = validate_zip_file(zip_bytes)
    print(f"  {'✓' if is_valid else '✗'} ZIP valide: {is_valid}")
    
    # Test extraction
    print("\n2.3 Extraction du contenu:")
    try:
        content = extract_zip_project(zip_bytes, max_files=10)
        print(f"  ✓ Contenu extrait: {len(content)} caractères")
        print(f"  Aperçu:")
        print(f"  {content[:300]}...")
    except Exception as e:
        print(f"  ✗ Erreur: {e}")


def test_api_models():
    """Test des modèles Django."""
    print("\n" + "="*80)
    print("TEST 3: Modèles Django")
    print("="*80)
    
    from apps.api.models import AnalysisSession
    
    print("\n3.1 Création d'une session de test:")
    try:
        session = AnalysisSession.objects.create(
            mode="A",
            input_type="text",
            input_source="Test",
            project_label="Test Project",
            status="pending",
        )
        print(f"  ✓ Session créée: ID={session.id}")
        print(f"  ✓ Mode: {session.get_mode_display()}")
        print(f"  ✓ Statut: {session.status}")
        
        # Mise à jour
        session.status = "completed"
        session.room_id = "test-room-123"
        session.decision = "VALIDER"
        session.save()
        print(f"  ✓ Session mise à jour")
        
        # Suppression
        session.delete()
        print(f"  ✓ Session supprimée")
        
    except Exception as e:
        print(f"  ✗ Erreur: {e}")


def test_mode_a_integration():
    """Test de l'intégration avec Mode A (Personne 1)."""
    print("\n" + "="*80)
    print("TEST 4: Intégration Mode A")
    print("="*80)
    
    print("\n4.1 Import du service orchestrateur:")
    try:
        from apps.orchestrator.services import run_security_audit_json
        print("  ✓ Service importé avec succès")
        
        print("\n4.2 Test avec un code simple:")
        test_code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # SQL Injection vulnerability!
    return execute_query(query)
"""
        
        print("  Code à analyser:")
        print("  " + "\n  ".join(test_code.strip().split("\n")))
        
        print("\n  Lancement de l'analyse Mode A...")
        print("  (Cela peut prendre 1-2 minutes)")
        
        result = run_security_audit_json(
            project_content=test_code,
            project_label="Test SQL Injection"
        )
        
        print(f"\n  ✓ Analyse terminée!")
        print(f"  Room ID: {result.get('room_id', 'N/A')}")
        print(f"  Décision: {result.get('decision', 'N/A')}")
        print(f"  Audit ID: {result.get('audit_id', 'N/A')}")
        print(f"  Nombre d'agents: {len(result.get('agents', []))}")
        
        if result.get('final_report'):
            print(f"\n  Rapport final (200 premiers caractères):")
            print(f"  {result['final_report'][:200]}...")
        
    except ImportError as e:
        print(f"  ✗ Service non disponible: {e}")
        print("  → Mode A pas encore configuré par Personne 1")
    except Exception as e:
        print(f"  ✗ Erreur: {e}")


def main():
    """Lance tous les tests."""
    print("\n" + "="*80)
    print("TESTS API BACKEND - PERSONNE 2")
    print("="*80)
    
    try:
        test_github_ingestion()
    except Exception as e:
        print(f"\n✗ Test GitHub échoué: {e}")
    
    try:
        test_zip_ingestion()
    except Exception as e:
        print(f"\n✗ Test ZIP échoué: {e}")
    
    try:
        test_api_models()
    except Exception as e:
        print(f"\n✗ Test modèles échoué: {e}")
    
    try:
        test_mode_a_integration()
    except Exception as e:
        print(f"\n✗ Test Mode A échoué: {e}")
    
    print("\n" + "="*80)
    print("TESTS TERMINÉS")
    print("="*80)
    print("\nPour tester l'API HTTP, lance le serveur:")
    print("  python manage.py runserver")
    print("\nPuis teste avec curl:")
    print('  curl -X POST http://127.0.0.1:8000/api/analyze/ \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"mode":"A","input_type":"text","content":"print(1)"}\'')
    print()


if __name__ == "__main__":
    main()

# Made with Bob
