"""Generate PDF reports for analyzed calls."""

import json
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from src.pipeline_models import SummaryResult
from src.database.models import Call, Report


SPACER_HEIGHT = 12


def generate_json(call: Call, report: Report, summary: SummaryResult) -> str:
    """Generate a call analysis report as a JSON string."""
    report_data = {
        "call": {
            "id": _get_value(call, "id"),
            "filename": _get_value(call, "filename"),
            "duration": _get_value(call, "duration"),
            "speaker_count": _get_value(call, "speaker_count"),
            "sentiment": _get_value(call, "sentiment"),
            "call_purpose": _get_value(call, "call_purpose"),
            "agent_behavior": _get_value(call, "agent_behavior"),
        },
        "summary": {
            "summary": _get_summary_text(summary, report),
            "agent_behavior": _get_value(
                summary,
                "agent_behavior",
                _get_value(call, "agent_behavior"),
            ),
            "key_entities": _get_value(summary, "key_entities", []),
            "key_discussion_points": _get_value(summary, "key_discussion_points", []),
            "action_items": _get_value(summary, "action_items", []),
            "resolution_status": _get_value(summary, "resolution_status"),
            "sentiment_trajectory": _get_value(summary, "sentiment_trajectory"),
        },
        "qa": {
            "overall_score": _get_value(report, "overall_score"),
            "empathy_score": _get_value(report, "empathy_score"),
            "resolution_score": _get_value(report, "resolution_score"),
            "compliance_score": _get_value(report, "compliance_score"),
            "communication_score": _get_value(report, "communication_score"),
            "professionalism_score": _get_value(report, "professionalism_score"),
            "compliance_flag": _get_value(report, "compliance_flag"),
        },
    }

    return json.dumps(report_data, indent=2)


def generate_pdf(call: Call, report: Report, summary: SummaryResult) -> bytes:
    """Generate a call analysis PDF and return it as bytes."""
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    story = [
        Paragraph("Call Center Intelligence Report", styles["Title"]),
        Spacer(1, SPACER_HEIGHT),
        Paragraph("Call Details", styles["Heading2"]),
        Paragraph(f"Filename: {_get_value(call, 'filename')}", styles["BodyText"]),
        Paragraph(f"Duration: {_get_value(call, 'duration')} seconds", styles["BodyText"]),
        Paragraph(f"Speaker Count: {_get_value(call, 'speaker_count')}", styles["BodyText"]),
        Paragraph(f"Sentiment: {_get_value(call, 'sentiment')}", styles["BodyText"]),
        Paragraph(f"Call Purpose: {_get_value(call, 'call_purpose')}", styles["BodyText"]),
        Spacer(1, SPACER_HEIGHT),
        Paragraph("Summary", styles["Heading2"]),
        Paragraph(_get_summary_text(summary, report), styles["BodyText"]),
        Spacer(1, SPACER_HEIGHT),
        Paragraph("Agent Behavior", styles["Heading2"]),
        Paragraph(
            _get_value(summary, "agent_behavior", _get_value(call, "agent_behavior")),
            styles["BodyText"],
        ),
        Spacer(1, SPACER_HEIGHT),
        Paragraph("QA Scores", styles["Heading2"]),
        Paragraph(f"Overall Score: {_get_value(report, 'overall_score')}", styles["BodyText"]),
        Paragraph(f"Empathy Score: {_get_value(report, 'empathy_score')}", styles["BodyText"]),
        Paragraph(f"Resolution Score: {_get_value(report, 'resolution_score')}", styles["BodyText"]),
        Paragraph(f"Compliance Score: {_get_value(report, 'compliance_score')}", styles["BodyText"]),
        Paragraph(f"Communication Score: {_get_value(report, 'communication_score')}", styles["BodyText"]),
        Paragraph(f"Professionalism Score: {_get_value(report, 'professionalism_score')}", styles["BodyText"]),
        Paragraph(f"Compliance Flag: {_get_value(report, 'compliance_flag')}", styles["BodyText"]),
        Spacer(1, SPACER_HEIGHT),
        Paragraph("Key Entities", styles["Heading2"]),
        Paragraph(_format_list(_get_value(summary, "key_entities", [])), styles["BodyText"]),
        Spacer(1, SPACER_HEIGHT),
        Paragraph("Action Items", styles["Heading2"]),
        Paragraph(_format_list(_get_value(summary, "action_items", [])), styles["BodyText"]),
    ]

    document.build(story)
    return buffer.getvalue()


def _get_summary_text(summary, report) -> str:
    """Return the best available summary text."""
    return _get_value(summary, "summary", _get_value(report, "summary"))


def _get_value(source, field_name: str, default="N/A"):
    """Read a field from an object or dictionary."""
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(field_name, default)

    return getattr(source, field_name, default)


def _format_list(values) -> str:
    """Format list values for a PDF paragraph."""
    if not values:
        return "N/A"

    if isinstance(values, str):
        return values

    return ", ".join(str(value) for value in values)
