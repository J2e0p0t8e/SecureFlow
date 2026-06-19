# API SecureFlow AI

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/analyze/` | Lance une analyse (modes A, B, C) |
| GET | `/api/session/<id>/` | Détail d'une session |
| GET | `/api/pdf/<room_id>/` | Télécharge le rapport PDF |
| GET | `/api/room/<room_id>/messages/` | Messages Band Room live |
| GET | `/api/health/` | Santé de l'API |

## POST /api/analyze/

**JSON** (texte ou GitHub) :
```json
{
  "mode": "A",
  "input_type": "text",
  "content": "...",
  "label": "mon-projet"
}
```

**Multipart** (ZIP) : champs `mode`, `input_type=zip`, `label`, `file`.

**Modes** :
- `A` — Audit sécurité (5 agents)
- `B` — Pipeline dev (6 agents)
- `C` — Rapport PDF (5 agents)

Voir [FONCTIONNEMENT_COMPLET.md](./FONCTIONNEMENT_COMPLET.md) pour le format de réponse détaillé.
