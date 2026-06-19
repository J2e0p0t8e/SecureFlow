"""Génération d'un rapport HTML autonome et stylé (téléchargeable .html)."""

from __future__ import annotations

import html
from typing import Any

from apps.core.markdown_lite import markdown_to_html
from apps.api.report_data import build_executive_summary, format_disagreement

_FAVICON_DATA_URI = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='64' y2='64' "
    "gradientUnits='userSpaceOnUse'%3E%3Cstop offset='0' stop-color='%237C3AED'/%3E"
    "%3Cstop offset='1' stop-color='%233B82F6'/%3E%3C/linearGradient%3E%3C/defs%3E"
    "%3Crect width='64' height='64' rx='15' fill='url(%23g)'/%3E"
    "%3Cpath d='M24 32.5 L29.5 38 L41 26' fill='none' stroke='%23ffffff' "
    "stroke-width='4.2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"
)

_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0d0c15;
  color: #ffffffcc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 880px; margin: 0 auto; padding: 48px 24px 80px; }
.brand { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.brand .dot {
  width: 34px; height: 34px; border-radius: 9px;
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  box-shadow: 0 6px 22px #7c3aed55;
}
.brand h1 { font-size: 20px; margin: 0; color: #fff; letter-spacing: .3px; }
.brand span { color: #ffffff66; font-size: 13px; }
.hero {
  background: linear-gradient(135deg, #7c3aed1a, #3b82f61a);
  border: 1px solid #7c3aed33;
  border-radius: 18px;
  padding: 28px;
  margin-bottom: 28px;
}
.hero h2 {
  margin: 0 0 6px; font-size: 26px;
  background: linear-gradient(135deg, #fff 40%, #a78bfa);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero .sub { color: #ffffff88; font-size: 14px; }
.badges { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 14px; border-radius: 999px;
  font-size: 13px; font-weight: 600;
  background: #ffffff0f; border: 1px solid #ffffff20; color: #fff;
}
.badge.crit { background: #ef44441f; border-color: #ef444455; color: #fca5a5; }
.badge.warn { background: #f59e0b1f; border-color: #f59e0b55; color: #fcd34d; }
.badge.ok   { background: #22c55e1f; border-color: #22c55e55; color: #86efac; }
.score-ring {
  display: inline-flex; align-items: baseline; gap: 4px;
  font-weight: 700; color: #fff;
}
.score-ring .n { font-size: 22px; }
.score-ring .u { font-size: 13px; color: #ffffff66; }
.meta {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px; margin-bottom: 36px;
}
.meta .cell {
  background: #ffffff08; border: 1px solid #ffffff15;
  border-radius: 12px; padding: 12px 14px;
}
.meta .k { color: #ffffff66; font-size: 11px; text-transform: uppercase; letter-spacing: .6px; }
.meta .v { color: #fff; font-size: 14px; margin-top: 4px; word-break: break-word; }
.section-title {
  font-size: 13px; text-transform: uppercase; letter-spacing: 1px;
  color: #a78bfa; margin: 40px 0 16px; font-weight: 700;
}
.agent {
  background: #ffffff06; border: 1px solid #ffffff15;
  border-radius: 14px; padding: 18px 20px; margin-bottom: 14px;
}
.agent h3 {
  margin: 0 0 12px; font-size: 16px; color: #fff;
  display: flex; align-items: center; gap: 10px;
}
.agent h3 .idx {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 7px; font-size: 12px;
  background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #fff;
}
.content { color: #ffffffcc; font-size: 14px; }
.content .md-heading { color: #e2e8f0; font-weight: 700; margin: 14px 0 6px; }
.content .md-h1 { font-size: 17px; }
.content .md-h2 { font-size: 15px; }
.content .md-h3, .content .md-h4 { font-size: 14px; }
.content .md-bullet { padding-left: 6px; margin: 2px 0; }
.final {
  background: linear-gradient(135deg, #7c3aed14, #3b82f614);
  border: 1px solid #7c3aed33; border-radius: 14px; padding: 22px;
}
.summary {
  background: linear-gradient(135deg, #7c3aed1f, #3b82f61a);
  border: 1px solid #7c3aed44; border-left: 4px solid #a78bfa;
  border-radius: 14px; padding: 22px 24px; margin-bottom: 28px;
}
.summary h3 { margin: 0 0 14px; font-size: 18px; color: #fff; }
.summary .rows { display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; margin-bottom: 14px; }
.summary .rows .k { color: #ffffff88; font-size: 13px; }
.summary .rows .v { color: #fff; font-size: 14px; font-weight: 600; }
.summary ul { margin: 6px 0 14px; padding-left: 20px; }
.summary li { margin: 3px 0; color: #ffffffcc; font-size: 14px; }
.summary .reco { color: #fff; font-size: 14px; }
.summary .reco b { color: #a78bfa; }
.disagree {
  background: #f973161a; border: 1px solid #f9731644;
  border-left: 4px solid #f97316; border-radius: 14px;
  padding: 18px 22px; margin-bottom: 28px;
}
.disagree h3 { margin: 0 0 12px; font-size: 16px; color: #fdba74; }
.disagree .rows { display: grid; grid-template-columns: max-content 1fr; gap: 5px 16px; margin-bottom: 10px; }
.disagree .rows .k { color: #ffffff88; font-size: 13px; }
.disagree .rows .v { color: #fff; font-size: 14px; font-weight: 600; }
.disagree .note { color: #ffffffcc; font-size: 13px; }
.footer {
  margin-top: 48px; padding-top: 20px; border-top: 1px solid #ffffff12;
  color: #ffffff44; font-size: 12px; text-align: center;
}
@media print {
  body { background: #fff; color: #111; }
  .hero, .final { background: #f4f0ff; }
  .agent, .meta .cell { background: #fff; border-color: #ddd; }
}
"""


def _decision_class(decision: str) -> str:
    text = (decision or "").upper()
    if any(k in text for k in ("CRIT", "REJET", "BLOCK", "DANGER", "FAIL")):
        return "crit"
    if any(k in text for k in ("CORRIG", "WARN", "REMÉD", "REMED", "ATTENTION", "REVIEW")):
        return "warn"
    if any(k in text for k in ("OK", "ACCEPT", "APPROUV", "PASS", "SAFE", "VALID")):
        return "ok"
    return ""


def _score_class(score: Any) -> str:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return ""
    if value >= 75:
        return "ok"
    if value >= 50:
        return "warn"
    return "crit"


def _cell(key: str, value: Any) -> str:
    if value in (None, "", 0):
        return ""
    return (
        f'<div class="cell"><div class="k">{html.escape(str(key))}</div>'
        f'<div class="v">{html.escape(str(value))}</div></div>'
    )


def _summary_block(summary: dict[str, Any]) -> str:
    takeaways = "".join(f"<li>{html.escape(str(t))}</li>" for t in summary.get("takeaways", []))
    return f"""
  <div class="summary">
    <h3>{html.escape(summary['title'])}</h3>
    <div class="rows">
      <span class="k">{html.escape(summary['verdict_label'])}</span><span class="v">{html.escape(summary['verdict'])}</span>
      <span class="k">{html.escape(summary['score_label'])}</span><span class="v">{html.escape(summary['score'])}</span>
      <span class="k">{html.escape(summary['agents_label'])}</span><span class="v">{html.escape(str(summary['agents']))}</span>
      <span class="k">{html.escape(summary['project_label'])}</span><span class="v">{html.escape(str(summary['project']))}</span>
    </div>
    <strong style="color:#ffffffaa;font-size:13px">{html.escape(summary['takeaways_label'])}</strong>
    <ul>{takeaways}</ul>
    <div class="reco"><b>{html.escape(summary['recommendation_label'])} :</b> {html.escape(summary['recommendation'])}</div>
  </div>"""


def _disagreement_block(dis: dict[str, Any] | None) -> str:
    if not dis:
        return ""
    rows = "".join(
        f'<span class="k">{html.escape(str(a))}</span><span class="v">{html.escape(str(v))}</span>'
        for a, v in dis["rows"]
    )
    spread = ""
    if dis.get("spread"):
        spread = (
            f'<span class="k">{html.escape(dis["spread_label"])}</span>'
            f'<span class="v">{html.escape(dis["spread"])}</span>'
        )
    return f"""
  <div class="disagree">
    <h3>⚠ {html.escape(dis['title'])}</h3>
    <div class="rows">{rows}{spread}</div>
    <div class="note">{html.escape(dis['note'])}</div>
  </div>"""


def render_report_html(ctx: dict[str, Any]) -> str:
    """Construit une page HTML autonome (CSS inline) à partir du contexte rapport."""
    audit_id = html.escape(str(ctx.get("audit_id", "")))
    decision = str(ctx.get("decision", "N/A"))
    decision_cls = _decision_class(decision)
    score = ctx.get("security_score")
    locale = ctx.get("locale", "fr")

    title_txt = "SecureFlow AI — Rapport d'audit" if locale != "en" else "SecureFlow AI — Audit Report"

    badges = [
        f'<span class="badge {decision_cls}">'
        f'{"Décision" if locale != "en" else "Decision"} : {html.escape(decision)}</span>'
    ]
    if score not in (None, ""):
        badges.append(
            f'<span class="badge {_score_class(score)}">'
            f'<span class="score-ring"><span class="n">{html.escape(str(score))}</span>'
            f'<span class="u">/100</span></span></span>'
        )

    meta_cells = "".join(
        [
            _cell("ID Audit", ctx.get("audit_id")),
            _cell("Room ID", ctx.get("room_id")),
            _cell("Date", ctx.get("date")),
            _cell("Mode", ctx.get("mode_display")),
            _cell("Entrée" if locale != "en" else "Input", ctx.get("input_type_display")),
            _cell("Projet" if locale != "en" else "Project", ctx.get("project_label")),
            _cell(
                "Durée" if locale != "en" else "Duration",
                f"{ctx['duration_seconds']}s" if ctx.get("duration_seconds") else "",
            ),
        ]
    )

    agents_html = []
    for i, agent in enumerate(ctx.get("agents", []), 1):
        name = html.escape(str(agent.get("name", "Agent")))
        body = markdown_to_html(agent.get("content") or "")
        agents_html.append(
            f'<div class="agent"><h3><span class="idx">{i}</span>{name}</h3>'
            f'<div class="content">{body}</div></div>'
        )

    agents_section = ""
    if agents_html:
        label = "Résultats des agents" if locale != "en" else "Agent results"
        agents_section = (
            f'<div class="section-title">{label}</div>' + "".join(agents_html)
        )

    final_label = "Rapport final" if locale != "en" else "Final report"
    final_html = markdown_to_html(ctx.get("final_report") or "")

    summary_html = _summary_block(build_executive_summary(ctx))
    disagree_html = _disagreement_block(format_disagreement(ctx.get("disagreement"), locale))

    footer = (
        "Généré automatiquement par SecureFlow AI"
        if locale != "en"
        else "Automatically generated by SecureFlow AI"
    )

    return f"""<!DOCTYPE html>
<html lang="{html.escape(str(locale))}" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#7C3AED">
<title>{title_txt} — {audit_id}</title>
<link rel="icon" type="image/svg+xml" href="{_FAVICON_DATA_URI}">
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <div class="dot"></div>
    <div><h1>SecureFlow AI</h1><span>{html.escape(title_txt)}</span></div>
  </div>

  <div class="hero">
    <h2>{html.escape(title_txt)}</h2>
    <div class="sub">{audit_id}</div>
    <div class="badges">{''.join(badges)}</div>
  </div>

  <div class="meta">{meta_cells}</div>

  {summary_html}

  {disagree_html}

  {agents_section}

  <div class="section-title">{final_label}</div>
  <div class="final"><div class="content">{final_html}</div></div>

  {summary_html}

  <div class="footer">{footer} — {audit_id}</div>
</div>
</body>
</html>
"""
