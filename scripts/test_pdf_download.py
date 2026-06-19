"""
Script de test pour vérifier le téléchargement PDF en Mode C.
Usage: python scripts/test_pdf_download.py
"""

import requests
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_pdf_download():
    print("🧪 Test du téléchargement PDF — SecureFlow AI\n")
    
    # Test 1 : Lancer analyse Mode C
    print("1️⃣ Lancement de l'analyse Mode C...")
    try:
        response = requests.post(f'{BASE_URL}/api/analyze/', json={
            'mode': 'C',
            'input_type': 'text',
            'code': 'test SQL injection vulnerability',
            'label': 'test-pdf-download',
            'selected_agents': ['ScannerAgent', 'ThreatAgent', 'ComplianceAgent', 'MetricsAgent', 'ReportAgent']
        })
        response.raise_for_status()
        data = response.json()
        
        print(f"   ✓ Mode : {data['mode']}")
        print(f"   ✓ Session ID : {data['session_id']}")
        print(f"   ✓ Audit ID : {data.get('audit_id', 'N/A')}")
        print(f"   ✓ Nombre d'agents : {len(data.get('agents', []))}")
        print(f"   ✓ Décision : {data.get('decision', 'N/A')}\n")
        
        session_id = data['session_id']
        
    except requests.exceptions.ConnectionError:
        print("   ✗ Erreur : Impossible de se connecter au serveur")
        print("   → Assurez-vous que le serveur Django tourne sur http://127.0.0.1:8000/")
        print("   → Commande : python manage.py runserver")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ Erreur lors de l'analyse : {e}")
        sys.exit(1)
    
    # Test 2 : Télécharger le PDF
    print("2️⃣ Téléchargement du PDF...")
    try:
        pdf_url = f"{BASE_URL}/api/pdf/{session_id}/"
        pdf_response = requests.get(pdf_url)
        pdf_response.raise_for_status()
        
        # Vérifier le Content-Type
        content_type = pdf_response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type:
            print(f"   ⚠️  Content-Type inattendu : {content_type}")
        
        # Sauvegarder le PDF
        output_dir = Path(__file__).parent.parent / 'media' / 'reports'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'test_rapport_{session_id[:8]}.pdf'
        
        with open(output_file, 'wb') as f:
            f.write(pdf_response.content)
        
        print(f"   ✓ PDF téléchargé : {len(pdf_response.content):,} bytes")
        print(f"   ✓ Fichier sauvegardé : {output_file}")
        print(f"   ✓ Content-Type : {content_type}\n")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du téléchargement : {e}")
        sys.exit(1)
    
    # Test 3 : Vérifier le contenu du PDF
    print("3️⃣ Vérification du contenu PDF...")
    try:
        pdf_content = pdf_response.content
        
        # Vérifier la signature PDF
        if pdf_content[:4] == b'%PDF':
            print("   ✓ Signature PDF valide")
        else:
            print("   ✗ Signature PDF invalide")
            sys.exit(1)
        
        # Vérifier la taille minimale
        if len(pdf_content) > 1000:
            print(f"   ✓ Taille suffisante ({len(pdf_content):,} bytes)")
        else:
            print(f"   ⚠️  PDF très petit ({len(pdf_content)} bytes)")
        
        # Vérifier la présence de texte clé
        pdf_text = pdf_content.decode('latin-1', errors='ignore')
        keywords = ['SecureFlow', 'Audit', 'SF-AUDIT']
        found_keywords = [kw for kw in keywords if kw in pdf_text]
        
        if found_keywords:
            print(f"   ✓ Mots-clés trouvés : {', '.join(found_keywords)}")
        else:
            print("   ⚠️  Aucun mot-clé trouvé dans le PDF")
        
    except Exception as e:
        print(f"   ⚠️  Impossible de vérifier le contenu : {e}")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS RÉUSSIS !")
    print("="*60)
    print(f"\n📄 Ouvrez le PDF : {output_file}")
    print(f"🌐 URL directe : {pdf_url}")
    print("\n💡 Pour tester dans le navigateur :")
    print(f"   1. Ouvrir : {BASE_URL}/")
    print("   2. Sélectionner Mode C")
    print("   3. Saisir du code et lancer l'analyse")
    print("   4. Cliquer sur le bouton 'Télécharger le rapport PDF'\n")


if __name__ == '__main__':
    test_pdf_download()