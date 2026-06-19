"""Tests de la conversion markdown légère (HTML / ReportLab)."""

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from apps.core.markdown_lite import markdown_to_reportlab


def _render(text: str) -> Paragraph:
    """Construit un Paragraph ReportLab : lève si le balisage est invalide."""
    return Paragraph(markdown_to_reportlab(text), getSampleStyleSheet()["Normal"])


def test_reportlab_escapes_angle_brackets():
    converted = markdown_to_reportlab('@orders_bp.route("/api/orders/<int:order_id>")')
    assert "<int:order_id>" not in converted
    assert "&lt;int:order_id&gt;" in converted
    # ne doit pas planter au parsing ReportLab
    _render('@orders_bp.route("/api/orders/<int:order_id>")')


def test_reportlab_escapes_ampersand():
    converted = markdown_to_reportlab("a && b < c")
    assert "&amp;&amp;" in converted
    _render("a && b < c")


def test_reportlab_keeps_bold_and_italic():
    converted = markdown_to_reportlab("**Verdict** : *surveiller* le `<pre>`")
    assert "<b>Verdict</b>" in converted
    assert "<i>surveiller</i>" in converted
    assert "&lt;pre&gt;" in converted
    _render("**Verdict** : *surveiller* le <pre>")


def test_reportlab_heading_with_code():
    converted = markdown_to_reportlab("## get_order(<int:id>)")
    assert converted.startswith("<b>")
    _render("## get_order(<int:id>)")
