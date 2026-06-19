"""Authentification API optionnelle."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest, JsonResponse


def check_api_key(request: HttpRequest) -> JsonResponse | None:
    """
    Si SECUREFLOW_API_KEY est défini, exige X-API-Key ou ?api_key=.
    Retourne None si la requête est autorisée.
    """
    expected = getattr(settings, "SECUREFLOW_API_KEY", "") or ""
    if not expected:
        return None
    provided = request.headers.get("X-API-Key") or request.GET.get("api_key") or ""
    if provided != expected:
        return JsonResponse({"error": "Clé API invalide ou manquante"}, status=401)
    return None
