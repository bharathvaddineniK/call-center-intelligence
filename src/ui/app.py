import shutil
from pathlib import Path
from uuid import uuid4

import gradio as gr
import config
from src.database.repository import (
    get_all_calls,
    get_recent_audit_logs,
    get_report_by_call_id,
)
from src.graph.pipeline import pipeline


PROCESSING_MESSAGE = """
### Processing call
Estimated duration: 1 to 3 minutes, depending on audio length and model latency.

Please do not refresh or close this page while the pipeline is running.
"""
AUDIT_LOG_HEADERS = ["Time", "Severity", "Event", "Call ID", "Message"]
EMPTY_AUDIT_LOG_ROWS = [["", "", "", "", ""]]


def copy_audio_to_data_dir(audio_path: str) -> str:
    """Copy a Gradio temp upload into the project audio directory."""
    source_path = Path(audio_path)
    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    if source_path.resolve().parent == config.AUDIO_DIR.resolve():
        return str(source_path)

    destination_path = config.AUDIO_DIR / f"{source_path.stem}_{uuid4().hex[:8]}{source_path.suffix}"
    shutil.copy2(source_path, destination_path)
    return str(destination_path)


def format_qa_scorecard(result: dict) -> str:
    """Format QA scores for display in the UI."""
    qa_scores = result.get("qa_scores") or {}

    return f"""
### QA Scorecard
- **Overall:** {result.get('overall_score', 'N/A')}
- **Empathy:** {qa_scores.get('empathy_score', 'N/A')}
- **Resolution:** {qa_scores.get('resolution_score', 'N/A')}
- **Compliance:** {qa_scores.get('compliance_score', 'N/A')}
- **Communication:** {qa_scores.get('communication_score', 'N/A')}
- **Professionalism:** {qa_scores.get('professionalism_score', 'N/A')}
- **Compliance Flag:** {result.get('compliance_flag', 'N/A')}
"""


def get_json_report_path(report_path: str | None):
    """Return the generated JSON report path that matches the PDF report."""
    if not report_path:
        return None

    json_path = Path(report_path).with_suffix(".json")
    return str(json_path) if json_path.exists() else None


def get_observability_data():
    """Read pipeline metrics and audit log from DB."""
    try:
        calls = get_all_calls(limit=1000)
        audit_logs = get_recent_audit_logs(limit=20)
        reports = [get_report_by_call_id(call.id) for call in calls]
        completed_reports = [report for report in reports if report is not None]
    except Exception as exc:
        return f"### Pipeline Metrics\nUnable to load observability data: {exc}", EMPTY_AUDIT_LOG_ROWS

    total_calls = len(calls)
    successful_calls = len(completed_reports)
    success_rate = (successful_calls / total_calls * 100) if total_calls else 0
    average_qa_score = (
        sum(report.overall_score for report in completed_reports) / successful_calls
        if successful_calls
        else 0
    )
    compliance_flags = sum(1 for report in completed_reports if report.compliance_flag)

    metrics_markdown = f"""
### Pipeline Metrics
| Metric | Value |
| --- | ---: |
| Total Calls | {total_calls} |
| Success Rate | {success_rate:.1f}% |
| Average QA Score | {average_qa_score:.1f} |
| Total Compliance Flags | {compliance_flags} |
"""

    audit_rows = [
        [
            audit_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            str(audit_log.severity),
            str(audit_log.event_type),
            str(audit_log.call_id or ""),
            str(audit_log.message),
        ]
        for audit_log in audit_logs
    ] or EMPTY_AUDIT_LOG_ROWS

    return metrics_markdown, audit_rows


def format_audit_log_markdown(audit_rows: list[list[str]]) -> str:
    """Format audit log rows as markdown to avoid Dataframe tab-render freezes."""
    if audit_rows == EMPTY_AUDIT_LOG_ROWS:
        return "### Audit Log\nNo audit events yet."

    lines = [
        "### Audit Log",
        "| Time | Severity | Event | Call ID | Message |",
        "| --- | --- | --- | --- | --- |",
    ]
    for time, severity, event, call_id, message in audit_rows:
        safe_message = message.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {time} | {severity} | {event} | {call_id} | {safe_message} |")

    return "\n".join(lines)


def get_observability_display():
    """Return observability metrics and audit log for Gradio display."""
    metrics_markdown, audit_rows = get_observability_data()
    return metrics_markdown, format_audit_log_markdown(audit_rows)


def run_pipeline(audio_path: str):
    """Run the call analysis pipeline for a Gradio-uploaded audio file."""
    if not audio_path:
        yield (
            gr.update(value="Please upload an audio file before analyzing.", visible=True),
            "",
            "",
            "",
            None,
            None,
        )
        return

    yield (
        gr.update(value=PROCESSING_MESSAGE, visible=True),
        "",
        "",
        "",
        None,
        None,
    )

    try:
        copied_audio_path = copy_audio_to_data_dir(audio_path)
        result = pipeline.invoke({"audio_path": copied_audio_path})
    except Exception as exc:
        yield (
            gr.update(value=f"**Pipeline failed:** {exc}", visible=True),
            "",
            "",
            "",
            None,
            None,
        )
        return

    if result.get("error"):
        error_message = f"**Pipeline failed:** {result['error']}"
        yield (
            gr.update(value=error_message, visible=True),
            "",
            "",
            "",
            None,
            None,
        )
        return
    if result.get("injection_detected"):
        yield (
            gr.update(value="**Injection attempt detected.** Pipeline stopped.", visible=True),
            "",
            "",
            "",
            None,
            None,
        )
        return

    transcript = result.get("transcript") or ""
    summary = result.get("summary") or "No summary was generated."
    report_path = result.get("report_path")
    json_report_path = get_json_report_path(report_path)
    qa_markdown = format_qa_scorecard(result)

    if result.get("supervisor_review_needed"):
        summary = f"{summary}\n\n**Supervisor review needed.**"

    yield (
        gr.update(value="Processing complete.", visible=True),
        transcript,
        summary,
        qa_markdown,
        report_path,
        json_report_path,
    )


with gr.Blocks() as app:
    with gr.Tab("Analyze call"):
        audio_input = gr.Audio(type="filepath", label="Upload audio")
        analyze_btn = gr.Button("Analyze")
        status_output = gr.Markdown(visible=False)
        transcript_output = gr.Textbox(label="Transcript")
        summary_output = gr.Markdown(label="Summary")
        qa_output = gr.Markdown(label="QA Scorecard")
        pdf_download = gr.File(label="Download PDF")
        json_download = gr.File(label="Download JSON")

        analyze_btn.click(
            fn=run_pipeline,
            inputs=[audio_input],
            outputs=[
                status_output,
                transcript_output,
                summary_output,
                qa_output,
                pdf_download,
                json_download,
            ],
        )
    with gr.Tab("Observability") as observability_tab:
        metrics_output = gr.Markdown()
        audit_log_output = gr.Markdown()
        refresh_observability_btn = gr.Button("Refresh")

        refresh_observability_btn.click(
            fn=get_observability_display,
            inputs=None,
            outputs=[metrics_output, audit_log_output],
            queue=False,
        )

        observability_tab.select(
            fn=get_observability_display,
            inputs=None,
            outputs=[metrics_output, audit_log_output],
            queue=False,
        )

    app.load(
        fn=get_observability_display,
        inputs=None,
        outputs=[metrics_output, audit_log_output],
        queue=False,
    )


app.queue()


if __name__ == "__main__":
    app.launch()
