"""
Module d'ingestion GitHub pour SecureFlow AI.
Récupère le contenu d'un repo GitHub public via l'API GitHub (sans token).
"""

import re
from typing import Optional
from urllib.parse import urlparse

import requests
from django.conf import settings


def parse_github_url(url: str) -> tuple[str, str, str]:
    """
    Parse une URL GitHub et retourne (owner, repo, branch).
    
    Exemples:
        https://github.com/user/repo -> (user, repo, main)
        https://github.com/user/repo/tree/dev -> (user, repo, dev)
    """
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    
    if len(path_parts) < 2:
        raise ValueError(f"URL GitHub invalide : {url}")
    
    owner = path_parts[0]
    repo = path_parts[1]
    
    # Détecter la branche si présente dans l'URL
    branch = "main"
    if len(path_parts) >= 4 and path_parts[2] == "tree":
        branch = path_parts[3]
    
    return owner, repo, branch


def fetch_github_project(
    url: str,
    max_files: int = 50,
    branch: Optional[str] = None,
) -> str:
    """
    Récupère le contenu d'un repo GitHub public et retourne une représentation textuelle.
    
    Args:
        url: URL du repo GitHub (ex: https://github.com/user/repo)
        max_files: Nombre maximum de fichiers à récupérer
        branch: Branche à utiliser (None = détection auto depuis URL ou 'main')
    
    Returns:
        String contenant le chemin et contenu de chaque fichier
    
    Raises:
        ValueError: URL invalide
        requests.HTTPError: Erreur API GitHub (404, 403, etc.)
    """
    owner, repo, detected_branch = parse_github_url(url)
    branch = branch or detected_branch
    
    # 1. Récupérer l'arbre des fichiers via API GitHub
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    
    try:
        response = requests.get(tree_url, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            # Essayer avec 'master' si 'main' échoue
            if branch == "main":
                return fetch_github_project(url, max_files, branch="master")
            raise ValueError(f"Repo ou branche introuvable : {owner}/{repo} (branche: {branch})")
        raise
    
    tree_data = response.json()
    
    if "tree" not in tree_data:
        raise ValueError(f"Réponse API GitHub invalide pour {owner}/{repo}")
    
    # 2. Filtrer et prioriser les fichiers
    files = []
    for item in tree_data["tree"]:
        if item["type"] != "blob":  # Ignorer les dossiers
            continue
        
        path = item["path"]
        
        # Ignorer les dossiers exclus
        path_parts = path.split("/")
        if any(part in settings.INGESTION_IGNORE_DIRS for part in path_parts):
            continue
        
        # Ignorer les fichiers binaires courants
        if path.endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe", ".dll", ".so")):
            continue
        
        files.append({"path": path, "url": item["url"]})
    
    # 3. Prioriser les fichiers importants
    priority_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".json", ".yml", ".yaml", ".md"}
    priority_names = {"requirements.txt", "package.json", "Dockerfile", "docker-compose.yml", "README.md"}
    
    def priority_score(file_info):
        path = file_info["path"]
        name = path.split("/")[-1]
        ext = "." + name.split(".")[-1] if "." in name else ""
        
        score = 0
        if name in priority_names:
            score += 100
        if ext in priority_extensions:
            score += 50
        if "test" not in path.lower():
            score += 10
        return score
    
    files.sort(key=priority_score, reverse=True)
    files = files[:max_files]
    
    # 4. Télécharger le contenu de chaque fichier
    project_content = f"# Projet GitHub : {owner}/{repo} (branche: {branch})\n"
    project_content += f"# Fichiers analysés : {len(files)}/{len(tree_data['tree'])}\n\n"
    
    for file_info in files:
        path = file_info["path"]
        
        # Utiliser raw.githubusercontent.com pour télécharger le contenu
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        
        try:
            content_response = requests.get(raw_url, timeout=5)
            content_response.raise_for_status()
            
            # Essayer de décoder en UTF-8, ignorer si binaire
            try:
                content = content_response.content.decode("utf-8")
            except UnicodeDecodeError:
                continue  # Ignorer les fichiers binaires
            
            project_content += f"\n{'='*80}\n"
            project_content += f"Fichier : {path}\n"
            project_content += f"{'='*80}\n"
            project_content += content
            project_content += f"\n\n"
            
        except Exception as e:
            # Continuer même si un fichier échoue
            project_content += f"\n[Erreur lors de la récupération de {path} : {e}]\n\n"
            continue
    
    return project_content


def is_valid_github_url(url: str) -> bool:
    """Vérifie si une URL est une URL GitHub valide."""
    pattern = r"^https?://github\.com/[\w\-]+/[\w\-\.]+/?.*$"
    return bool(re.match(pattern, url))

# Made with Bob
