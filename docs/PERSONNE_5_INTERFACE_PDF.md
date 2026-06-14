# Personne 5 — Interface, PDF & Déploiement

> Tu construis l'interface web, l'affichage live Band Room, le PDF Mode C, et le déploiement public.

---

## Ton rôle en une phrase

Formulaire (3 modes) → appeler l'API Personne 2 → afficher la Band Room en direct → PDF téléchargeable (Mode C) → URL publique pour la démo.

---

## Dossiers où tu codes

```
templates/               ← pages HTML Django (TON CODE)
static/                  ← CSS, JS (TON CODE)
apps/api/views.py        ← ajouter endpoint PDF si besoin (avec Pers. 2)
media/reports/           ← PDF générés (créer au runtime)
```

**Ne touche pas à :** `apps/agents/`, `apps/orchestrator/`, `apps/ingestion/` (sauf consommation API).

Branche Git : `personne-5-interface-pdf`

---

## Installation

```powershell
cd "Band G.U.A.R.D"
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# reportlab déjà dans requirements.txt
python manage.py migrate
python manage.py runserver
```

Ouvre : http://127.0.0.1:8000/

---

## Variables `.env` dont tu as besoin

Tu **n'as pas** besoin de créer d'agents Band toi-même. Tu utilises le `.env` partagé de l'équipe.

Pour développer l'interface en local :

```env
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Pour le déploiement (Render / Railway) :

```env
DJANGO_DEBUG=False
ALLOWED_HOSTS=ton-app.onrender.com,127.0.0.1
# + toutes les variables Band + GROQ du .env équipe
```

---

## Contrat API — Personne 2

Tu appelles **uniquement** le backend Django. Exemple :

### Lancer une analyse

```javascript
// static/js/analyze.js
const response = await fetch("/api/analyze/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    mode: "A",                    // "A" | "B" | "C"
    input_type: "github",         // "github" | "zip" | "text"
    github_url: "https://github.com/user/repo",
    label: "mon-projet",
  }),
});
const data = await response.json();
// data.room_id  → pour affichage Band live
// data.agents   → liste des réponses agents
// data.decision → Mode A
// data.final_report → texte final
```

### Réponse Mode A (exemple)

```json
{
  "mode": "A",
  "room_id": "e93506d9-3597-4c8f-bd65-35c14712d0d5",
  "decision": "CORRIGER",
  "audit_id": "SF-AUDIT-20260614-4521",
  "final_report": "DÉCISION FINALE : ...",
  "agents": [
    {"name": "ScannerAgent", "content": "SCAN TERMINÉ : ..."},
    {"name": "ThreatAgent", "content": "..."}
  ]
}
```

Coordonne avec Personne 2 le format **exact** avant J4.

---

## Page principale — structure UI

### Formulaire

| Champ | Description |
|-------|-------------|
| Sélecteur mode | A = Audit · B = Dev pipeline · C = Rapport PDF |
| Input type | GitHub URL / Upload ZIP / Coller code |
| Bouton | `Analyser` / `Lancer` |

### Zone résultats

1. **Band Room live** — fil de messages agents
2. **Résumé** — décision, score, audit ID
3. **Mode C** — bouton `Télécharger PDF`

---

## Band Room live — comment afficher

Quand l'API retourne `room_id`, interroge périodiquement le backend :

### Option A — endpoint dédié (à créer avec Pers. 2)

```
GET /api/room/{room_id}/messages/
```

Personne 2 peut implémenter :

```python
from apps.agents.band_registry import get_band_client_for

def room_messages(request, room_id):
    client = get_band_client_for("ScannerAgent")  # n'importe quel agent participant
    messages = client.get_context(room_id)
    return JsonResponse({"messages": messages})
```

### Option B — polling côté front sur la réponse API

Si l'analyse est **synchrone** (attente 1–3 min), afficher directement `data.agents[]` à la fin.

Pour la **démo hackathon**, Option B suffit au début. Option A pour l'effet "live" pendant l'exécution.

### Affichage visuel

```html
<!-- templates/partials/agent_message.html -->
<div class="agent-card agent-{{ name|lower }}">
  <strong>{{ name }}</strong>
  <pre>{{ content }}</pre>
</div>
```

Couleurs distinctes par agent (Scanner=bleu, Threat=rouge, etc.).

---

## Mode C — génération PDF (ReportLab)

Personne 4 livre le **contenu texte** via `ReportAgent`. Toi tu génères le **fichier PDF**.

### Dépendance

Déjà installée : `reportlab>=4.0.0`

### Module suggéré

```python
# apps/api/pdf_generator.py (ou apps/core/pdf.py)
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_audit_pdf(title: str, report_text: str, audit_id: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>SecureFlow AI — Rapport d'audit</b>", styles["Title"]),
        Paragraph(f"ID : {audit_id}", styles["Normal"]),
        Spacer(1, 12),
    ]
    for line in report_text.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace("<", "&lt;"), styles["Normal"]))
            story.append(Spacer(1, 6))
    doc.build(story)
    return buffer.getvalue()
```

### Endpoint téléchargement

```python
# apps/api/views.py
from django.http import HttpResponse

def download_pdf(request, session_id):
    session = AnalysisSession.objects.get(pk=session_id)
    pdf_bytes = generate_audit_pdf(
        title="Audit sécurité",
        report_text=session.result_json["final_report"],
        audit_id=session.result_json.get("audit_id", "N/A"),
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="secureflow-rapport.pdf"'
    return response
```

---

## Déploiement (Render ou Railway)

### Fichiers à ajouter

```
Procfile                 ← web: gunicorn secureflow.wsgi (ou manage.py runserver dev)
render.yaml              ← optionnel
requirements.txt         ← déjà prêt
```

### Variables d'environnement sur Render

Copier **tout** le `.env` équipe dans le dashboard Render :

- `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`
- Les 13 `BAND_*_*`
- `GROQ_API_KEY`, `LLM_PROVIDER`

### Test post-déploiement

1. Ouvrir l'URL publique
2. Mode A + `scripts/sample_flask.py` équivalent
3. Vérifier Band Room + résultat

Coordonne avec **Personne 1** avant le push final (J6).

---

## Vidéo de démo (J7) — structure 4 min

| Temps | Contenu |
|-------|---------|
| 0:00–0:30 | Problème + solution SecureFlow |
| 0:30–1:00 | Architecture (13 agents Band) |
| 1:00–3:30 | Démo live des 3 modes sur URL publique |
| 3:30–4:00 | Valeur business + Band AI |

Prépare **à l'avance** 3 exemples testés (pas d'improvisation).

---

## Coordination

| Avec | Sujet |
|------|--------|
| **Personne 2** | Contrat `POST /api/analyze/`, endpoint messages Room |
| **Personne 4** | Format `RAPPORT FINAL :` pour PDF |
| **Personne 1** | Validation déploiement J6 |

---

## Livrables

| Jour | Livrable |
|------|----------|
| J2 | Page HTML + formulaire mode |
| J3 | Affichage résultats agents |
| J4 | PDF Mode C + branchement API |
| J6 | App déployée URL publique |
| J7 | Vidéo + slides |

---

## Erreurs fréquentes

| Problème | Solution |
|----------|----------|
| CORS | Même domaine front/API ou configurer django-cors-headers |
| Timeout navigateur | Afficher loader + analyse synchrone longue |
| PDF vide | Vérifier `final_report` dans réponse Mode C |
| CSS absent | `python manage.py collectstatic` en prod |
