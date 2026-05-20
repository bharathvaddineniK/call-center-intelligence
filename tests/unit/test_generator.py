import json
from unittest.mock import MagicMock

from src.pipeline_models import CallReport, SummaryResult
from src.services.reports.generator import build_call_report, generate_json, generate_pdf


def create_mock_call():
    """Create a mock Call object for report generator tests."""
    call = MagicMock()
    call.id = 1
    call.filename = "call_114.mp3"
    call.duration = 60.0
    call.speaker_count = 2
    call.sentiment = "neutral"
    call.call_purpose = "support"
    call.agent_behavior = "The agent was helpful."
    return call


def create_mock_report():
    """Create a mock Report object for report generator tests."""
    report = MagicMock()
    report.summary = "The caller needed help with internet service."
    report.overall_score = 85.0
    report.empathy_score = 90.0
    report.resolution_score = 80.0
    report.compliance_score = 85.0
    report.communication_score = 88.0
    report.professionalism_score = 92.0
    report.compliance_flag = True
    report.compliance_severity = "medium"
    report.violation_description = "Caller verification was incomplete"
    report.timestamp_evidence = ["00:15"]
    return report


def create_summary_result():
    """Create a SummaryResult object for report generator tests."""
    return SummaryResult(
        summary="The caller needed help with internet service.",
        sentiment="neutral",
        agent_behavior="The agent was helpful.",
        key_entities=["internet"],
        call_purpose="support",
        key_discussion_points=["Caller reported an issue", "Agent offered help"],
        action_items=["Agent to follow up"],
        resolution_status="resolved",
        sentiment_trajectory="Neutral -> Positive",
    )


def test_generate_pdf_returns_bytes():
    """Generate a PDF report as bytes."""
    result = generate_pdf(
        call=create_mock_call(),
        report=create_mock_report(),
        summary=create_summary_result(),
    )

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_json_returns_valid_json():
    """Generate a JSON report that parses with expected top-level keys."""
    result = generate_json(
        call=create_mock_call(),
        report=create_mock_report(),
        summary=create_summary_result(),
    )

    parsed_result = json.loads(result)

    assert "call" in parsed_result
    assert "summary" in parsed_result
    assert "qa" in parsed_result
    assert parsed_result["call"]["filename"] == "call_114.mp3"
    assert parsed_result["summary"]["summary"] == "The caller needed help with internet service."
    assert parsed_result["qa"]["overall_score"] == 85.0
    assert parsed_result["qa"]["compliance_severity"] == "medium"
    assert parsed_result["qa"]["violation_description"] == "Caller verification was incomplete"
    assert parsed_result["qa"]["timestamp_evidence"] == ["00:15"]


def test_build_call_report_returns_pydantic_model():
    """Assemble a strongly typed CallReport model."""
    result = build_call_report(
        call=create_mock_call(),
        report=create_mock_report(),
        summary=create_summary_result(),
    )

    assert isinstance(result, CallReport)
    assert result.call.filename == "call_114.mp3"
    assert result.qa.compliance_flag is True
