"""
Module d'ingestion ZIP pour SecureFlow AI.
Extrait et analyse le contenu d'un fichier ZIP uploadé.
"""

import zipfile
from io import BytesIO
from pathlib import Path

from django.conf import settings


def extract_zip_project(file_bytes: bytes, max_files: int = 50) -> str:
    """
    Extrait le contenu d'un fichier ZIP et retourne une représentation textuelle.
    
    Args:
        file_bytes: Contenu binaire du fichier ZIP
        max_files: Nombre maximum de fichiers à extraire
    
    Returns:
        String contenant le chemin et contenu de chaque fichier
    
    Raises:
        zipfile.BadZipFile: Fichier ZIP invalide ou corrompu
    """
    try:
        zip_buffer = BytesIO(file_bytes)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            # 1. Lister tous les fichiers
            all_files = []
            for file_info in zip_file.filelist:
                # Ignorer les dossiers
                if file_info.is_dir():
                    continue
                
                path = file_info.filename
                
                # Ignorer les fichiers système macOS/Windows
                if "/__MACOSX/" in path or path.startswith("__MACOSX/"):
                    continue
                if path.endswith(".DS_Store") or path.endswith("Thumbs.db"):
                    continue
                
                # Ignorer les dossiers exclus
                path_parts = Path(path).parts
                if any(part in settings.INGESTION_IGNORE_DIRS for part in path_parts):
                    continue
                
                # Ignorer les fichiers binaires courants
                if path.endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", 
                                 ".exe", ".dll", ".so", ".pyc", ".class", ".o")):
                    continue
                
                # Ignorer les fichiers trop gros (> 1MB)
                if file_info.file_size > 1_000_000:
                    continue
                
                all_files.append({"path": path, "size": file_info.file_size})
            
            # 2. Prioriser les fichiers importants
            priority_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".env", 
                                  ".json", ".yml", ".yaml", ".md", ".txt"}
            priority_names = {"requirements.txt", "package.json", "Dockerfile", 
                            "docker-compose.yml", "README.md", ".env", ".env.example"}
            
            def priority_score(file_info):
                path = file_info["path"]
                name = Path(path).name
                ext = Path(path).suffix.lower()
                
                score = 0
                if name in priority_names:
                    score += 100
                if ext in priority_extensions:
                    score += 50
                if "test" not in path.lower():
                    score += 10
                # Favoriser les fichiers à la racine
                if len(Path(path).parts) <= 2:
                    score += 20
                return score
            
            all_files.sort(key=priority_score, reverse=True)
            selected_files = all_files[:max_files]
            
            # 3. Extraire le contenu
            project_content = f"# Projet ZIP uploadé\n"
            project_content += f"# Fichiers analysés : {len(selected_files)}/{len(all_files)}\n\n"
            
            for file_info in selected_files:
                path = file_info["path"]
                
                try:
                    # Lire le contenu du fichier
                    content_bytes = zip_file.read(path)
                    
                    # Essayer de décoder en UTF-8
                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        # Essayer d'autres encodages courants
                        try:
                            content = content_bytes.decode("latin-1")
                        except:
                            # Ignorer si impossible à décoder
                            continue
                    
                    project_content += f"\n{'='*80}\n"
                    project_content += f"Fichier : {path}\n"
                    project_content += f"{'='*80}\n"
                    project_content += content
                    project_content += f"\n\n"
                    
                except Exception as e:
                    # Continuer même si un fichier échoue
                    project_content += f"\n[Erreur lors de la lecture de {path} : {e}]\n\n"
                    continue
            
            return project_content
            
    except zipfile.BadZipFile:
        raise ValueError("Fichier ZIP invalide ou corrompu")
    except Exception as e:
        raise ValueError(f"Erreur lors de l'extraction du ZIP : {str(e)}")


def validate_zip_file(file_bytes: bytes) -> bool:
    """
    Vérifie si les bytes correspondent à un fichier ZIP valide.
    
    Args:
        file_bytes: Contenu binaire à vérifier
    
    Returns:
        True si c'est un ZIP valide, False sinon
    """
    try:
        zip_buffer = BytesIO(file_bytes)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            # Tester l'intégrité
            bad_file = zip_file.testzip()
            return bad_file is None
    except:
        return False

# Made with Bob
