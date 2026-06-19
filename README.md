# SecureFlow AI

**SecureFlow AI** helps European SaaS teams pass GDPR/OWASP compliance audits without blocking their roadmap — and automatically fixes what it finds, under human supervision.

Hackathon **Band of Agents 2026** (`BANDHACK26`) — Track 3: Regulated & High-Stakes Workflows.

## Product — Audit-to-Fix (single pipeline)

One unified pipeline where **phase evolves during execution** (not a fixed agent list chosen upfront):

| Phase | What happens in Band Room |
|-------|---------------------------|
| Scanning | ScannerAgent maps attack surface |
| Triage | ThreatAgent confirms vulnerabilities; optional **dynamic recruitment** of ComplianceAgent / RiskAgent |
| Decision | DecisionAgent rules GO/NO-GO; **disagreements** between agents are posted explicitly in Band |
| Human gate | If CRITIQUE/CORRIGER → operator approves in Band before remediation |
| Remediation | DevAgent → SecurityAgent → QAAgent → patch **ZIP** |
| Reporting | MetricsAgent → ReportAgent → formal **PDF** (clean/watch branch) |

**Band is the source of truth** — agents read `get_context()` from the Room; Python fallback only if Band is empty.

## Stack

- Python / Django
- **Band AI** — coordination layer (recruitment, escalations, human decisions, disagreements)
- Google Gemini / Groq (LLM)
- ReportLab (PDF)

## Start

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) and [docs/FONCTIONNEMENT_COMPLET.md](./docs/FONCTIONNEMENT_COMPLET.md).
