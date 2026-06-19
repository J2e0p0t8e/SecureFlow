"""
Pipeline unifié Audit-to-Fix — Band comme source de vérité.

Phases :
  scanning → triage → decision → (CRITIQUE|CORRIGER: remediation) | (clean: reporting) → done

Recrutement dynamique dans Band après Threat (Compliance, Risk, Decision, remédiation…).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from apps.agents.base import AgentResult, BaseAgent
from apps.agents.band_client import BandRoom
from apps.agents.band_registry import load_credentials, resolve_handle
from apps.agents.mode_a import ComplianceAgent, DecisionAgent, RiskAgent, ScannerAgent, ThreatAgent
from apps.agents.mode_b import DevAgent, QAAgent, SecurityAgent
from apps.agents.mode_c import MetricsAgent, ReportAgent
from apps.core.agent_output import (
    extract_audit_id,
    extract_decision,
    extract_metadata_json,
    extract_risk_score,
    generate_id,
    needs_remediation,
)
from apps.core.pipeline_context import (
    add_warning,
    get_ingestion_meta,
    get_locale,
    get_static_signal,
    init_pipeline_context,
    set_disagreement_context,
    set_pipeline_phase,
)
from apps.ingestion.bundle import prepare_project_for_scan
from apps.orchestrator.base import threat_needs_rescan
from apps.orchestrator.exceptions import HumanReviewPending, HumanReviewRequired

logger = logging.getLogger(__name__)

AUDIT_TO_FIX_BAND_AGENTS = [
    "ScannerAgent",
    "ThreatAgent",
    "ComplianceAgent",
    "RiskAgent",
    "DecisionAgent",
    "DevAgent",
    "SecurityAgent",
    "QAAgent",
    "MetricsAgent",
    "ReportAgent",
]

_PAYMENT_KEYWORDS = re.compile(
    r"\b(stripe|paypal|payment|paiement|checkout|pci[- ]?dss|carte bancaire|credit card)\b",
    re.IGNORECASE,
)

_AGENT_TASK_BRIEF: dict[str, dict[str, str]] = {
    "ScannerAgent": {
        "fr": "cartographie de la surface d'attaque et des dépendances",
        "en": "attack surface and dependency mapping",
    },
    "ThreatAgent": {
        "fr": "triage des menaces OWASP / STRIDE",
        "en": "OWASP / STRIDE threat triage",
    },
    "ComplianceAgent": {
        "fr": "conformité RGPD et exigences réglementaires",
        "en": "GDPR and regulatory compliance",
    },
    "RiskAgent": {
        "fr": "scoring de risque et arbitrage",
        "en": "risk scoring and arbitration",
    },
    "DecisionAgent": {
        "fr": "verdict GO / NO-GO et plan d'action",
        "en": "GO / NO-GO verdict and action plan",
    },
    "DevAgent": {
        "fr": "patch de remédiation (fichiers corrigés)",
        "en": "remediation patch (corrected files)",
    },
    "SecurityAgent": {
        "fr": "revue sécurité du patch",
        "en": "security review of the patch",
    },
    "QAAgent": {
        "fr": "validation QA du patch",
        "en": "QA validation of the patch",
    },
    "MetricsAgent": {
        "fr": "score sécurité formel /100",
        "en": "formal security score /100",
    },
    "ReportAgent": {
        "fr": "rapport final client",
        "en": "final client report",
    },
}


def _task_brief(agent_name: str, locale: str) -> str:
    lang = "en" if locale == "en" else "fr"
    return (_AGENT_TASK_BRIEF.get(agent_name) or {}).get(lang, "")


@dataclass
class AuditToFixRunResult:
    room_id: str
    results: list[AgentResult] = field(default_factory=list)
    audit_id: str | None = None
    decision: str | None = None
    risk_score: float | None = None
    phase: str = "done"
    branch: str | None = None
    security_score: float | None = None
    recruited_agents: list[str] = field(default_factory=list)
    disagreement: dict[str, Any] | None = None

    @property
    def final_report(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].content

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mode": "A",
            "product": "audit-to-fix",
            "room_id": self.room_id,
            "phase": self.phase,
            "branch": self.branch,
            "decision": self.decision,
            "audit_id": self.audit_id,
            "final_report": self.final_report,
            "agents": [
                {"name": item.agent_name, "content": item.content}
                for item in self.results
            ],
            "pipeline_agents": [item.agent_name for item in self.results],
            "recruited_agents": self.recruited_agents,
            "ingestion": get_ingestion_meta(),
            "locale": get_locale(),
        }
        if self.risk_score is not None:
            payload["risk_score"] = self.risk_score
        if self.security_score is not None:
            payload["security_score"] = self.security_score
        if self.disagreement:
            payload["disagreement"] = self.disagreement
        return payload


def _agent_result_dicts(results: list[AgentResult]) -> list[dict[str, str]]:
    return [{"name": r.agent_name, "content": r.content} for r in results]


def _result_by_name(results: list[AgentResult], name: str) -> AgentResult | None:
    matches = [r for r in results if r.agent_name == name]
    return matches[-1] if matches else None


def _band_text(key: str, locale: str, **kwargs: Any) -> str:
    """Messages de coordination Band (recrutement, escalade) localisés."""
    catalog: dict[str, dict[str, str]] = {
        "pii_detected": {
            "fr": "ThreatAgent signale des données personnelles (PII/RGPD).",
            "en": "ThreatAgent flagged personal data (PII/GDPR).",
        },
        "high_threat_score": {
            "fr": "Score menace élevé ({score}/10) — conformité RGPD/OWASP requise.",
            "en": "High threat score ({score}/10) — GDPR/OWASP compliance required.",
        },
        "pii_keywords": {
            "fr": "Mentions PII/RGPD détectées dans le rapport Threat.",
            "en": "PII/GDPR keywords detected in Threat report.",
        },
        "risk_score_recruit": {
            "fr": "Risque global {score}/10 — RiskAgent recruté pour arbitrage.",
            "en": "Overall risk {score}/10 — RiskAgent recruited for arbitration.",
        },
        "payment_pci": {
            "fr": "Domaine paiement/PCI détecté — RiskAgent recruté.",
            "en": "Payment/PCI domain detected — RiskAgent recruited.",
        },
        "pci_review": {
            "fr": "ThreatAgent demande une revue PCI-DSS.",
            "en": "ThreatAgent requests PCI-DSS review.",
        },
        "threat_after_scanner": {
            "fr": "Scanner a cartographié la surface d'attaque — ThreatAgent requis.",
            "en": "Scanner mapped the attack surface — ThreatAgent required.",
        },
        "decision_after_compliance": {
            "fr": "Triage conformité terminé — DecisionAgent requis pour arbitrer.",
            "en": "Compliance triage complete — DecisionAgent required to arbitrate.",
        },
        "decision_after_risk": {
            "fr": "Analyse de risque terminée — DecisionAgent doit trancher.",
            "en": "Risk analysis complete — DecisionAgent must decide.",
        },
        "decision_final": {
            "fr": "Analyse terminée — DecisionAgent recruté pour trancher GO/NO-GO.",
            "en": "Analysis complete — DecisionAgent recruited for GO/NO-GO decision.",
        },
        "remediation_recruit": {
            "fr": "Remédiation approuvée — {agent} rejoint la Room.",
            "en": "Remediation approved — {agent} joins the Room.",
        },
        "rescan_post_fix": {
            "fr": "Re-scan post-remédiation pour valider les corrections.",
            "en": "Post-remediation re-scan to validate fixes.",
        },
        "metrics_clean": {
            "fr": "Projet propre ou surveillé — MetricsAgent pour score formel /100.",
            "en": "Clean or watch project — MetricsAgent for formal /100 score.",
        },
        "report_final": {
            "fr": "Rapport final client — ReportAgent recruté.",
            "en": "Final client report — ReportAgent recruited.",
        },
        "static_high_recruit": {
            "fr": "SAST Bandit : {high} vulnérabilité(s) HIGH détectée(s) — ComplianceAgent recruté.",
            "en": "Bandit SAST: {high} HIGH severity issue(s) found — ComplianceAgent recruited.",
        },
        "static_signal_risk": {
            "fr": "Analyse statique : {total} signaux objectifs (plancher de risque {floor}/10) — RiskAgent recruté.",
            "en": "Static analysis: {total} objective signals (risk floor {floor}/10) — RiskAgent recruited.",
        },
        "crosscheck_override": {
            "fr": (
                "CROSS-CHECK : le SAST a détecté {high} vulnérabilité(s) HIGH non couvertes "
                "par le verdict « {decision} ». Remédiation forcée pour ne rien laisser passer."
            ),
            "en": (
                "CROSS-CHECK: SAST found {high} HIGH severity issue(s) not covered by the "
                "« {decision} » verdict. Remediation enforced as a safety net."
            ),
        },
    }
    lang = "en" if locale == "en" else "fr"
    template = catalog.get(key, {}).get(lang) or catalog.get(key, {}).get("fr") or key
    return template.format(**kwargs) if kwargs else template


def _should_recruit_compliance(threat: AgentResult) -> tuple[bool, str]:
    locale = get_locale()
    meta = extract_metadata_json(threat.content)
    if meta.get("contains_pii") is True:
        return True, _band_text("pii_detected", locale)
    score = extract_risk_score(threat.content, meta)
    if score is not None and score > 6:
        return True, _band_text("high_threat_score", locale, score=score)
    signal = get_static_signal() or {}
    if signal.get("high", 0) >= 1:
        return True, _band_text("static_high_recruit", locale, high=signal["high"])
    upper = threat.content.upper()
    if any(k in upper for k in ("PII", "RGPD", "GDPR", "DONNÉES PERSONNELLES", "PERSONAL DATA")):
        return True, _band_text("pii_keywords", locale)
    return False, ""


def _should_recruit_risk(threat: AgentResult, project_content: str) -> tuple[bool, str]:
    locale = get_locale()
    meta = extract_metadata_json(threat.content)
    score = extract_risk_score(threat.content, meta)
    if score is not None and score > 5:
        return True, _band_text("risk_score_recruit", locale, score=score)
    if _PAYMENT_KEYWORDS.search(project_content) or _PAYMENT_KEYWORDS.search(threat.content):
        return True, _band_text("payment_pci", locale)
    if meta.get("requires_pci") is True:
        return True, _band_text("pci_review", locale)
    signal = get_static_signal() or {}
    if signal.get("risk_floor", 0) >= 6:
        return True, _band_text(
            "static_signal_risk",
            locale,
            total=signal.get("total", 0),
            floor=signal.get("risk_floor", 0),
        )
    return False, ""


def _detect_disagreement(results: list[AgentResult]) -> dict[str, Any] | None:
    scores: dict[str, float] = {}
    for name in ("ThreatAgent", "ComplianceAgent", "RiskAgent"):
        item = _result_by_name(results, name)
        if not item:
            continue
        meta = extract_metadata_json(item.content)
        score = extract_risk_score(item.content, meta)
        if score is not None:
            scores[name] = score
    if len(scores) < 2:
        return None
    values = list(scores.values())
    if max(values) - min(values) < 3:
        return None
    return {"scores": scores, "spread": round(max(values) - min(values), 1)}


def _collect_remediation_scope(results: list[AgentResult]) -> str:
    parts: list[str] = []
    for name in ("ScannerAgent", "ThreatAgent", "DecisionAgent"):
        item = _result_by_name(results, name)
        if item and item.content.strip():
            parts.append(f"=== {name} ===\n{item.content.strip()}")
    return "\n\n".join(parts)


class AuditToFixOrchestrator:
    """Audit régulé → décision → remédiation ou rapport, avec recrutement Band dynamique."""

    def __init__(self) -> None:
        self.scanner = ScannerAgent()
        self.threat = ThreatAgent()
        self.compliance = ComplianceAgent()
        self.risk = RiskAgent()
        self.decision = DecisionAgent()
        self.dev = DevAgent()
        self.security = SecurityAgent()
        self.qa = QAAgent()
        self.metrics = MetricsAgent()
        self.report = ReportAgent()
        self.recruited: set[str] = {"ScannerAgent"}

    def _recruit(
        self,
        room_id: str,
        agent: BaseAgent,
        *,
        reason: str,
        from_agent: BaseAgent | None = None,
    ) -> None:
        if agent.name in self.recruited:
            return
        source = from_agent or self.threat
        creds = load_credentials(agent.name)
        if not creds.agent_id:
            raise ValueError(f"Agent ID manquant pour {agent.name}")
        source.band.add_participant(room_id, creds.agent_id)
        locale = get_locale()
        try:
            source.band.post_recruitment(
                room_id,
                recruited_agent_name=agent.name,
                reason=reason,
                locale=locale,
                from_agent_name=source.name,
            )
        except Exception as exc:
            logger.warning("post_recruitment: %s", exc)
        self.recruited.add(agent.name)
        logger.info("Recruté dans Band : %s ← %s", agent.name, source.name)

    def _post_pass_the_ball(
        self,
        room_id: str,
        from_agent: BaseAgent,
        to_agent: BaseAgent,
    ) -> None:
        locale = get_locale()
        try:
            from_agent.band.post_pass_the_ball(
                room_id,
                from_agent_name=from_agent.name,
                to_agent_name=to_agent.name,
                locale=locale,
                task_brief=_task_brief(to_agent.name, locale),
            )
        except Exception as exc:
            logger.warning("post_pass_the_ball %s→%s: %s", from_agent.name, to_agent.name, exc)

    def _emit_progress(
        self,
        on_progress: Callable[[dict], None] | None,
        *,
        phase: str,
        agent: str | None = None,
        results: list[AgentResult],
        next_agent: str | None = None,
        extra: dict | None = None,
    ) -> None:
        if not on_progress:
            return
        payload: dict[str, Any] = {
            "workflow_phase": phase,
            "agent": agent,
            "next_agent": next_agent,
            "agents": _agent_result_dicts(results),
            "recruited_agents": sorted(self.recruited),
        }
        if extra:
            payload.update(extra)
        on_progress(payload)

    def _agent_by_name(self, name: str | None) -> BaseAgent | None:
        if not name:
            return None
        for agent in (
            self.scanner,
            self.threat,
            self.compliance,
            self.risk,
            self.decision,
            self.dev,
            self.security,
            self.qa,
            self.metrics,
            self.report,
        ):
            if agent.name == name:
                return agent
        return None

    def _run_agent(
        self,
        room_id: str,
        agent: BaseAgent,
        *,
        next_agent: BaseAgent | None,
        results: list[AgentResult],
        workflow_phase: str,
        on_progress: Callable[[dict], None] | None,
        prior_agent_name: str | None = None,
        wrap_up_message: str = "",
        extra_input: str | None = None,
    ) -> AgentResult:
        set_pipeline_phase(workflow_phase)
        locale = get_locale()
        if prior_agent_name is None and results:
            prior_agent_name = results[-1].agent_name
        prior_agent = self._agent_by_name(prior_agent_name)

        if on_progress:
            on_progress(
                {
                    "phase": "started",
                    "workflow_phase": workflow_phase,
                    "agent": agent.name,
                    "next_agent": next_agent.name if next_agent else None,
                    "agents": _agent_result_dicts(results),
                    "recruited_agents": sorted(self.recruited),
                }
            )
        result = agent.run(
            room_id,
            next_agent=next_agent,
            prior_agent=prior_agent,
            extra_input=extra_input,
        )
        results.append(result)

        if next_agent:
            self._post_pass_the_ball(room_id, agent, next_agent)
        elif wrap_up_message or agent.name in ("DecisionAgent", "ReportAgent", "QAAgent"):
            try:
                agent.band.post_agent_wrap_up(
                    room_id,
                    agent_name=agent.name,
                    locale=locale,
                    message=wrap_up_message,
                )
            except Exception as exc:
                logger.warning("post_agent_wrap_up %s: %s", agent.name, exc)

        if on_progress:
            on_progress(
                {
                    "phase": "completed",
                    "workflow_phase": workflow_phase,
                    "agent": result.agent_name,
                    "next_agent": next_agent.name if next_agent else None,
                    "agents": _agent_result_dicts(results),
                    "recruited_agents": sorted(self.recruited),
                }
            )
        return result

    def _maybe_rescan(
        self,
        room_id: str,
        threat_result: AgentResult,
        results: list[AgentResult],
        *,
        rescan_done: bool,
        on_progress: Callable[[dict], None] | None,
    ) -> bool:
        if rescan_done or not threat_needs_rescan(threat_result.content):
            return rescan_done

        locale = get_locale()
        msg = (
            "ThreatAgent requests targeted re-scan (multiple P1 or RE-SCAN). "
            "@mention Scanner for confirmation."
            if locale == "en"
            else "ThreatAgent demande un second scan ciblé (P1 multiples ou RE-SCAN). "
            "@mention Scanner pour confirmation."
        )
        creds = load_credentials("ScannerAgent")
        try:
            self.scanner.band.post_escalation(
                room_id,
                from_agent="ThreatAgent",
                message=msg,
                target_agent_id=creds.agent_id,
                target_handle=resolve_handle("ScannerAgent") or creds.handle,
                target_name="ScannerAgent",
            )
        except Exception as exc:
            logger.warning("post_escalation: %s", exc)

        rescan = self._run_agent(
            room_id,
            self.scanner,
            next_agent=self.threat,
            results=results,
            workflow_phase="re_scanning",
            on_progress=on_progress,
        )
        logger.info("Escalade → second Scanner (%s chars)", len(rescan.content))
        if on_progress:
            on_progress(
                {
                    "phase": "completed",
                    "workflow_phase": "re_scanning",
                    "agent": rescan.agent_name,
                    "agents": _agent_result_dicts(results),
                    "escalation": "threat_rescan",
                    "recruited_agents": sorted(self.recruited),
                }
            )
        return True

    def _run_triage(
        self,
        room_id: str,
        initial_content: str,
        results: list[AgentResult],
        on_progress: Callable[[dict], None] | None,
    ) -> list[AgentResult]:
        self._recruit(
            room_id,
            self.threat,
            reason=_band_text("threat_after_scanner", get_locale()),
            from_agent=self.scanner,
        )

        scan_bundle = prepare_project_for_scan(
            initial_content,
            get_ingestion_meta(),
            locale=get_locale(),
        )

        self._run_agent(
            room_id,
            self.scanner,
            next_agent=self.threat,
            results=results,
            workflow_phase="scanning",
            on_progress=on_progress,
            extra_input=scan_bundle,
        )

        threat_result = self._run_agent(
            room_id,
            self.threat,
            next_agent=None,
            results=results,
            workflow_phase="triage",
            on_progress=on_progress,
        )

        rescan_done = False
        rescan_done = self._maybe_rescan(
            room_id, threat_result, results, rescan_done=rescan_done, on_progress=on_progress
        )

        recruit_compliance, reason_c = _should_recruit_compliance(threat_result)
        recruit_risk, reason_r = _should_recruit_risk(threat_result, initial_content)

        if recruit_compliance:
            first_next = self.compliance
        elif recruit_risk:
            first_next = self.risk
        else:
            first_next = self.decision
        self._post_pass_the_ball(room_id, self.threat, first_next)

        if recruit_compliance:
            self._recruit(room_id, self.compliance, reason=reason_c, from_agent=self.threat)
            if not recruit_risk:
                self._recruit(
                    room_id,
                    self.decision,
                    reason=_band_text("decision_after_compliance", get_locale()),
                    from_agent=self.threat,
                )
            next_after_compliance = self.risk if recruit_risk else self.decision
            self._run_agent(
                room_id,
                self.compliance,
                next_agent=next_after_compliance,
                results=results,
                workflow_phase="triage",
                on_progress=on_progress,
            )

        if recruit_risk:
            self._recruit(room_id, self.risk, reason=reason_r, from_agent=self.threat)
            if "DecisionAgent" not in self.recruited:
                self._recruit(
                    room_id,
                    self.decision,
                    reason=_band_text("decision_after_risk", get_locale()),
                    from_agent=self.threat,
                )
            self._run_agent(
                room_id,
                self.risk,
                next_agent=self.decision,
                results=results,
                workflow_phase="triage",
                on_progress=on_progress,
            )

        disagreement = _detect_disagreement(results)
        if disagreement:
            locale = get_locale()
            set_disagreement_context(disagreement)
            try:
                self.threat.band.post_disagreement(
                    room_id, disagreement=disagreement, locale=locale
                )
            except Exception as exc:
                logger.warning("post_disagreement: %s", exc)

        if "DecisionAgent" not in self.recruited:
            self._recruit(
                room_id,
                self.decision,
                reason=_band_text("decision_final", get_locale()),
                from_agent=self.threat,
            )
        self._run_agent(
            room_id,
            self.decision,
            next_agent=None,
            results=results,
            workflow_phase="decision",
            on_progress=on_progress,
        )
        return results

    @staticmethod
    def _mention_list(agent: BaseAgent) -> list[dict[str, Any]]:
        creds = load_credentials(agent.name)
        handle = resolve_handle(agent.name) or creds.handle
        if not creds.agent_id or not handle:
            return []
        return [
            {
                "id": creds.agent_id,
                "handle": handle.lstrip("@"),
                "name": agent.name,
            }
        ]

    @staticmethod
    def _remediation_brief_message(scope: str, locale: str) -> str:
        handle = resolve_handle("DevAgent") or "DevAgent"
        if locale == "en":
            body = (
                f"@{handle.lstrip('@')}\n\n"
                "**REMEDIATION BRIEF**\n\n"
                "Return corrected files (=== FILE: path === blocks) for flagged issues only.\n\n"
                f"{scope[:5500]}"
            )
        else:
            body = (
                f"@{handle.lstrip('@')}\n\n"
                "**BRIEF REMÉDIATION**\n\n"
                "Renvoie les fichiers corrigés (blocs === FILE: chemin ===) "
                "uniquement pour les problèmes signalés.\n\n"
                f"{scope[:5500]}"
            )
        return body

    def _run_remediation(
        self,
        room_id: str,
        results: list[AgentResult],
        on_progress: Callable[[dict], None] | None,
    ) -> list[AgentResult]:
        scope = _collect_remediation_scope(results)
        locale = get_locale()
        mentions = self._mention_list(self.dev)
        try:
            self.decision.band.post_message(
                room_id,
                content=self._remediation_brief_message(scope, locale),
                mentions=mentions,
            )
        except Exception as exc:
            logger.warning("remediation brief: %s", exc)

        for agent, nxt, phase in (
            (self.dev, self.security, "remediating"),
            (self.security, self.qa, "remediating"),
            (self.qa, None, "remediating"),
        ):
            self._recruit(
                room_id,
                agent,
                reason=_band_text("remediation_recruit", locale, agent=agent.name),
            )
            self._run_agent(
                room_id,
                agent,
                next_agent=nxt,
                results=results,
                workflow_phase=phase,
                on_progress=on_progress,
            )

        self._recruit(
            room_id,
            self.scanner,
            reason=_band_text("rescan_post_fix", get_locale()),
        )
        self._run_agent(
            room_id,
            self.scanner,
            next_agent=None,
            results=results,
            workflow_phase="re_scanning",
            on_progress=on_progress,
        )
        return results

    def _run_reporting(
        self,
        room_id: str,
        results: list[AgentResult],
        on_progress: Callable[[dict], None] | None,
    ) -> list[AgentResult]:
        self._recruit(
            room_id,
            self.metrics,
            reason=_band_text("metrics_clean", get_locale()),
        )
        self._run_agent(
            room_id,
            self.metrics,
            next_agent=self.report,
            results=results,
            workflow_phase="reporting",
            on_progress=on_progress,
        )
        self._recruit(
            room_id,
            self.report,
            reason=_band_text("report_final", get_locale()),
        )
        self._run_agent(
            room_id,
            self.report,
            next_agent=None,
            results=results,
            workflow_phase="reporting",
            on_progress=on_progress,
        )
        return results

    def _human_gate_remediation(
        self,
        *,
        room_id: str,
        results: list[AgentResult],
        decision: str,
        initial_content: str,
        initial_label: str,
        ingestion_meta: dict | None,
    ) -> None:
        locale = get_locale()
        if locale == "en":
            reason = (
                f"Decision: {decision}. Human approval is required before automated "
                "remediation (DevAgent patch generation)."
            )
        else:
            reason = (
                f"Décision : {decision}. Validation humaine requise avant la remédiation "
                "automatisée (génération de correctifs par DevAgent)."
            )
        try:
            self.scanner.band.ensure_owner_participant(room_id)
            self.scanner.band.post_human_review_request(room_id, reason=reason, locale=locale)
        except Exception as exc:
            logger.warning("post_human_review_request: %s", exc)
            add_warning(f"Band human review event failed: {exc}")

        pending = HumanReviewPending(
            room_id=room_id,
            project_content=initial_content,
            project_label=initial_label,
            resume_from_index=0,
            reason=reason,
            results=list(results),
            ingestion_meta=ingestion_meta,
            locale=locale,
            workflow_mode="A",
            review_kind="pre_remediation",
            branch="remediation",
            decision=decision,
        )
        raise HumanReviewRequired(pending)

    def _crosscheck_decision(self, room_id: str, decision: str | None) -> str | None:
        """Filet de sécurité : le SAST objectif prime sur un verdict LLM trop clément.

        Si Bandit a trouvé des vulnérabilités HIGH mais que la décision ne déclenche
        pas de remédiation, on force l'escalade et on l'annonce dans la Band Room.
        """
        signal = get_static_signal() or {}
        high = int(signal.get("high", 0) or 0)
        if high < 1 or needs_remediation(decision):
            return decision

        forced = "CRITIQUE" if high >= 3 else "CORRIGER"
        self._forced_decision = forced
        locale = get_locale()
        try:
            self.decision.band.post_disagreement(
                room_id,
                disagreement={
                    "scores": {"SAST-Bandit": high, "DecisionAgent": 0},
                    "spread": high,
                },
                locale=locale,
            )
        except Exception as exc:
            logger.warning("crosscheck post_disagreement: %s", exc)
        try:
            self.decision.band.post_agent_discussion(
                room_id,
                agent_name=self.decision.name,
                content=_band_text(
                    "crosscheck_override",
                    locale,
                    high=high,
                    decision=decision or "N/A",
                ),
                reply_to_agent_name=None,
                locale=locale,
            )
        except Exception as exc:
            logger.warning("crosscheck discussion: %s", exc)
        add_warning(
            f"Cross-check SAST: {high} HIGH findings → décision forcée {forced} "
            f"(verdict LLM initial: {decision})."
        )
        return forced

    def run(
        self,
        initial_content: str,
        *,
        task_id: str | None = None,
        initial_label: str = "Projet",
        on_room_created: Callable[[str], None] | None = None,
        on_progress: Callable[[dict], None] | None = None,
        ingestion_meta: dict | None = None,
        locale: str | None = None,
        resume_branch: str | None = None,
        existing_results: list[AgentResult] | None = None,
        existing_room_id: str | None = None,
        skip_human_gate: bool = False,
    ) -> AuditToFixRunResult:
        init_pipeline_context(ingestion_meta, workflow_mode="A", locale=locale)
        results: list[AgentResult] = list(existing_results or [])
        disagreement = _detect_disagreement(results)
        self._forced_decision: str | None = None

        if resume_branch == "remediation" and existing_room_id:
            room_id = existing_room_id
            self.recruited = set(
                (ingestion_meta or {}).get("_recruited")
                or [r.agent_name for r in results]
            )
            set_pipeline_phase("remediating")
            results = self._run_remediation(room_id, results, on_progress)
            phase = "done"
            branch = "remediation"
        elif resume_branch == "reporting" and existing_room_id:
            room_id = existing_room_id
            self.recruited = set(
                (ingestion_meta or {}).get("_recruited")
                or [r.agent_name for r in results]
            )
            results = self._run_reporting(existing_room_id, results, on_progress)
            phase = "done"
            branch = "reporting"
        else:
            room = self.scanner.band.create_room(task_id=task_id)
            room_id = room.id
            logger.info("Room %s — Audit-to-Fix (Scanner lead)", room_id)
            self.scanner.band.ensure_owner_participant(room_id)
            if on_room_created:
                on_room_created(room_id)
            try:
                self.scanner.band.seed_room(
                    room_id, initial_content, label=initial_label, locale=get_locale()
                )
            except Exception as exc:
                logger.warning("seed_room: %s", exc)

            results = self._run_triage(room_id, initial_content, [], on_progress)
            disagreement = _detect_disagreement(results)

            decision_result = _result_by_name(results, "DecisionAgent")
            content = decision_result.content if decision_result else ""
            metadata = extract_metadata_json(content)
            decision = extract_decision(content, metadata)
            raw_score = metadata.get("risk_score")
            risk_score = float(raw_score) if isinstance(raw_score, (int, float)) else None

            decision = self._crosscheck_decision(room_id, decision)

            if decision and needs_remediation(decision):
                if not skip_human_gate:
                    self._human_gate_remediation(
                        room_id=room_id,
                        results=results,
                        decision=decision,
                        initial_content=initial_content,
                        initial_label=initial_label,
                        ingestion_meta=ingestion_meta,
                    )
                set_pipeline_phase("remediating")
                results = self._run_remediation(room_id, results, on_progress)
                phase = "done"
                branch = "remediation"
            else:
                set_pipeline_phase("reporting")
                results = self._run_reporting(room_id, results, on_progress)
                phase = "done"
                branch = "reporting"

        decision_result = _result_by_name(results, "DecisionAgent")
        content = decision_result.content if decision_result else ""
        metadata = extract_metadata_json(content)
        audit_id = extract_audit_id(content, metadata) or generate_id("SF-AUDIT")
        decision = extract_decision(content, metadata)
        if self._forced_decision:
            decision = self._forced_decision
        raw_score = metadata.get("risk_score")
        risk_score = float(raw_score) if isinstance(raw_score, (int, float)) else None

        report_result = _result_by_name(results, "ReportAgent")
        security_score = None
        if report_result:
            report_meta = extract_metadata_json(report_result.content)
            sec = report_meta.get("security_score") or report_meta.get("score")
            if isinstance(sec, (int, float)):
                security_score = float(sec)

        return AuditToFixRunResult(
            room_id=room_id,
            results=results,
            audit_id=audit_id,
            decision=decision,
            risk_score=risk_score,
            phase=phase,
            branch=branch,
            security_score=security_score,
            recruited_agents=sorted(self.recruited),
            disagreement=disagreement,
        )
