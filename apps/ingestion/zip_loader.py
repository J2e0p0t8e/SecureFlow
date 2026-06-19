"""
Module d'ingestion ZIP pour SecureFlow AI.
Extrait et analyse le contenu d'un fichier ZIP uploadé.
"""

import zipfile
from io import BytesIO
from pathlib import Path

from django.conf import settings

from apps.ingestion.bundle import truncate_file_body
from apps.ingestion.selectors import build_file_manifest, is_binary_path, select_paths
from apps.ingestion.types import IngestionResult


def _is_safe_zip_path(path: str) -> bool:
    """Rejette les chemins absolus et les traversées (zip slip)."""
    normalized = path.replace("\\", "/")
    if normalized.startswith("/") or ".." in normalized.split("/"):
        return False
    return True


def extract_zip_project(file_bytes: bytes, max_files: int = 50) -> IngestionResult:
    """
    Extrait le contenu d'un fichier ZIP et retourne une représentation textuelle.

    Args:
        file_bytes: Contenu binaire du fichier ZIP
        max_files: Nombre maximum de fichiers à extraire

    Returns:
        IngestionResult avec inventaire, manifeste et contenu priorisé

    Raises:
        zipfile.BadZipFile: Fichier ZIP invalide ou corrompu
    """
    try:
        zip_buffer = BytesIO(file_bytes)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            all_paths: list[str] = []
            for file_info in zip_file.filelist:
                if file_info.is_dir():
                    continue

                path = file_info.filename
                if not _is_safe_zip_path(path):
                    continue
                if "/__MACOSX/" in path or path.startswith("__MACOSX/"):
                    continue
                if path.endswith(".DS_Store") or path.endswith("Thumbs.db"):
                    continue

                path_parts = Path(path).parts
                if any(part in settings.INGESTION_IGNORE_DIRS for part in path_parts):
                    continue
                if is_binary_path(path):
                    continue
                if file_info.file_size > 1_000_000:
                    continue

                all_paths.append(path)

            selected_paths, truncated = select_paths(all_paths, max_files)
            manifest = build_file_manifest(all_paths, selected_paths)
            selected_set = set(selected_paths)

            project_content = "# Projet ZIP uploadé\n"
            project_content += f"# Fichiers analysés : {len(selected_paths)}/{len(all_paths)}\n\n"
            project_content += manifest
            project_content += "\n\n"

            for file_info in zip_file.filelist:
                if file_info.is_dir():
                    continue
                path = file_info.filename
                if path not in selected_set:
                    continue

                try:
                    content_bytes = zip_file.read(path)
                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            content = content_bytes.decode("latin-1")
                        except UnicodeDecodeError:
                            continue

                    content = truncate_file_body(content, path)
                    project_content += f"\n{'=' * 80}\n"
                    project_content += f"Fichier : {path}\n"
                    project_content += f"{'=' * 80}\n"
                    project_content += content
                    project_content += "\n\n"

                except Exception as exc:
                    project_content += f"\n[Erreur lors de la lecture de {path} : {exc}]\n\n"
                    continue

            if not selected_paths:
                raise ValueError("Aucun fichier texte récupérable dans le ZIP")

            return IngestionResult(
                content=project_content,
                files_analyzed=len(selected_paths),
                files_total=len(all_paths),
                truncated=truncated,
                source_label="zip:upload",
                file_manifest=manifest,
            )

    except zipfile.BadZipFile:
        raise ValueError("Fichier ZIP invalide ou corrompu")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Erreur lors de l'extraction du ZIP : {str(exc)}") from exc


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
            bad_file = zip_file.testzip()
            return bad_file is None
    except zipfile.BadZipFile:
        return False
    except Exception:
        return False
