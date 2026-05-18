from pathlib import Path
from types import SimpleNamespace

import config
from src.agents.qa_scorer import score_with_usage
from src.agents.summarizer import summarize_with_usage
from src.database.models import (
    CALL_STATUS_BLOCKED,
    CALL_STATUS_COMPLETED,
    CALL_STATUS_FAILED,
    CALL_STATUS_FLAGGED,
)
from src.database.repository import (
    get_call_by_hash,
    save_call,
    save_failed_call,
    save_report,
    update_call_metadata,
    update_call_status,
)
from src.pipeline_models import PipelineState, SummaryResult
from src.services.audio.cleanup import cleanup_old_files
from src.services.audio.diarization import assign_speakers
from src.services.audio.transcriber import get_transcription
from src.services.audio.validator import validate_audio
from src.services.reports.generator import generate_json, generate_pdf
from src.services.security.audit_logger import (
    EVENT_INJECTION_SCAN,
    EVENT_INTAKE,
    EVENT_PII_SCAN,
    EVENT_PIPELINE,
    EVENT_QA_SCORING,
    EVENT_REPORT_GENERATION,
    EVENT_SUMMARY,
    EVENT_SUPERVISOR_REVIEW,
    EVENT_TRANSCRIPTION,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    log_event,
)
from src.services.security.injection_detector import get_matched_patterns
from src.services.security.pii_redactor import redact_pii


def _redact_metadata(state: PipelineState) -> tuple[str | None, str | None]:
    """Return caller metadata after applying the same PII redaction policy."""
    caller_id = _redact_metadata_value(state.get("caller_id"))
    department = _redact_metadata_value(state.get("department"))
    return caller_id, department


def _redact_metadata_value(value: str | None) -> str | None:
    if not value:
        return None

    redacted_value, _ = redact_pii(value)
    return redacted_value


def intake_node(state: PipelineState) -> dict:
    """Validates the audio and returns the duration of the audio"""
    try:
        audio_path = state["audio_path"]
        result = validate_audio(audio_path)
        
        if not result.is_valid:
            log_event(
                event_type=EVENT_INTAKE, 
                message=f"Intake failed: {result.error}", 
                severity=SEVERITY_ERROR
            )
            return {"error": result.error, "error_logged": True}
        
        log_event(
            event_type=EVENT_INTAKE, 
            message=f"Intake validated: {audio_path}", 
            severity=SEVERITY_INFO
        )
        
        return {
            "duration": result.duration
        }
    except Exception as e:
        log_event(
            event_type=EVENT_INTAKE, 
            message=str(e), 
            severity=SEVERITY_ERROR
        )
        return {"error": str(e), "error_logged": True}
    
def transcription_node(state: PipelineState) -> dict:
    try:
        audio_path = state["audio_path"]
        result = get_transcription(audio_path)
        segments_with_speakers = assign_speakers(result.segments)

        log_event(
            event_type=EVENT_TRANSCRIPTION,
            message=f"Transcript ready via {result.source} with confidence {result.confidence}",
            severity=SEVERITY_INFO
        )

        return {
            "file_hash": result.file_hash,
            "transcript": result.text,
            "segments": segments_with_speakers,
            "confidence": result.confidence,
            "speaker_count": len(
                {
                    segment.get("speaker")
                    for segment in segments_with_speakers
                    if segment.get("speaker")
                }
            ),
        }
    except Exception as e:
        log_event(
            event_type=EVENT_TRANSCRIPTION, 
            message=str(e), 
            severity=SEVERITY_ERROR
        )
        return {"error": f"Transcription failed: {str(e)}", "error_logged": True}
    
def injection_check_node(state: PipelineState) -> dict:
    """Checks the audio transcription for any prompt injection"""

    try:
        matched_patterns = get_matched_patterns(state["transcript"])
        if matched_patterns:
            log_event(
                event_type=EVENT_INJECTION_SCAN,
                message=f"Injection detected: {', '.join(matched_patterns)}",
                severity=SEVERITY_WARNING
            )

            return {
                "injection_detected": True,
                "injection_patterns": matched_patterns,
            }
        
        log_event(
            event_type=EVENT_INJECTION_SCAN,
            message="No injection detected",
            severity=SEVERITY_INFO
        )

        return {
            "injection_detected": False,
            "injection_patterns": [],
        }
    except Exception as e:
        log_event(
            event_type=EVENT_INJECTION_SCAN,
            message=str(e),
            severity=SEVERITY_ERROR
        )
        return {"error": str(e), "error_logged": True}

def pii_redaction_node(state: PipelineState) -> dict:
    """Reacts the PII with placeholders"""

    try:
        redacted_text, pii_detected = redact_pii(state["transcript"])

        redacted_segments = []

        for segment in state["segments"]:
            redacted_segment_text, _ = redact_pii(segment["text"])
            redacted_segments.append({**segment, "text": redacted_segment_text})
        
        if pii_detected:
            log_event(
                event_type=EVENT_PII_SCAN,
                message="PII redacted",
                severity=SEVERITY_WARNING,
            )
        else:
            log_event(
                event_type=EVENT_PII_SCAN,
                message="No PII detected",
                severity=SEVERITY_INFO,
            )

        return {
            "transcript": redacted_text,
            "segments": redacted_segments,
            "pii_detected": pii_detected
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PII_SCAN,
            message=str(e),
            severity=SEVERITY_ERROR
        )
        return {"error": str(e), "error_logged": True}
    
def summarize_qa_node(state: PipelineState) -> dict:
    """Summarize the transcript and return summary and QA state fields."""

    transcript = state["transcript"]

    try:
        summary, summary_usage = summarize_with_usage(transcript)

        log_event(
            event_type=EVENT_SUMMARY,
            message="Summary generated",
            severity=SEVERITY_INFO,
        )
    except Exception as e:
        log_event(
            event_type=EVENT_SUMMARY,
            message=f"Summary failed: {str(e)}",
            severity=SEVERITY_ERROR,
        )
        return {"error": str(e), "error_logged": True}

    try:
        qa_score, qa_usage = score_with_usage(transcript, summary)

        log_event(
            event_type=EVENT_QA_SCORING,
            message=f"QA scoring complete with overall score {qa_score.overall_score}",
            severity=SEVERITY_INFO,
        )

        return {
            "summary": summary.summary,
            "sentiment": summary.sentiment,
            "agent_behavior": summary.agent_behavior,
            "call_purpose": summary.call_purpose, 
            "qa_scores": {
                "empathy_score": qa_score.empathy_score,
                "resolution_score": qa_score.resolution_score,
                "compliance_score": qa_score.compliance_score,
                "communication_score": qa_score.communication_score,
                "professionalism_score": qa_score.professionalism_score,
            },
            "overall_score": qa_score.overall_score,
            "compliance_flag": qa_score.compliance_flag,
            "summary_json": summary.model_dump_json(),
            "token_usage": {
                "summary": summary_usage,
                "qa": qa_usage,
            },
        }
    except Exception as e:
        log_event(
            event_type=EVENT_QA_SCORING,
            message=f"QA scoring failed: {str(e)}",
            severity=SEVERITY_ERROR,
        )
        return {"error": str(e), "error_logged": True}
    
def report_node(state: PipelineState) -> dict:
    """Persist call/report records and generate report files."""
    try:
        file_hash = state["file_hash"]
        transcript = state["transcript"]
        segments = state["segments"]
        confidence = state["confidence"]
        duration = state["duration"]
        speaker_count = state["speaker_count"]
        sentiment = state["sentiment"]
        call_purpose = state["call_purpose"]
        agent_behavior = state["agent_behavior"]
        summary_text = state["summary"]
        qa_scores = state["qa_scores"]
        overall_score = state["overall_score"]
        compliance_flag = state["compliance_flag"]
        summary_json = state["summary_json"]
        call_status = (
            CALL_STATUS_FLAGGED
            if state.get("supervisor_review_needed")
            else CALL_STATUS_COMPLETED
        )
        caller_id, department = _redact_metadata(state)

        audio_path = state["audio_path"]
        filename = Path(audio_path).name

        existing_call = get_call_by_hash(file_hash)
        if existing_call:
            call_id = existing_call.id
            update_call_status(call_id, call_status)
            update_call_metadata(
                call_id,
                caller_id=caller_id,
                department=department,
            )
        else:
            call_id = save_call(
                filename=filename,
                file_hash=file_hash,
                duration=duration,
                transcription=transcript,
                speaker_count=speaker_count,
                sentiment=sentiment,
                call_purpose=call_purpose,
                agent_behavior=agent_behavior,
                status=call_status,
                segments=segments,
                confidence=confidence,
                caller_id=caller_id,
                department=department,
            )

        summary = SummaryResult.model_validate_json(summary_json)
        call = SimpleNamespace(
            id=call_id,
            filename=filename,
            duration=duration,
            speaker_count=speaker_count,
            sentiment=sentiment,
            call_purpose=call_purpose,
            agent_behavior=agent_behavior,
        )
        report = SimpleNamespace(
            summary=summary_text,
            overall_score=overall_score,
            empathy_score=qa_scores["empathy_score"],
            resolution_score=qa_scores["resolution_score"],
            compliance_score=qa_scores["compliance_score"],
            communication_score=qa_scores["communication_score"],
            professionalism_score=qa_scores["professionalism_score"],
            compliance_flag=compliance_flag,
        )

        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = config.REPORTS_DIR / f"{Path(filename).stem}_report.pdf"
        json_path = config.REPORTS_DIR / f"{Path(filename).stem}_report.json"
        pdf_bytes = generate_pdf(call, report, summary)
        json_str = generate_json(call, report, summary)
        json_path.write_text(json_str)
        report_path.write_bytes(pdf_bytes)

        save_report(
            call_id=call_id,
            overall_score=overall_score,
            empathy_score=qa_scores["empathy_score"],
            resolution_score=qa_scores["resolution_score"],
            compliance_score=qa_scores["compliance_score"],
            communication_score=qa_scores["communication_score"],
            professionalism_score=qa_scores["professionalism_score"],
            summary=summary_text,
            compliance_flag=compliance_flag,
            pdf_path=str(report_path),
        )
        cleanup_old_files(
            str(config.AUDIO_DIR),
            max_age_hours=config.MAX_AUDIO_AGE_HOURS,
            filename_pattern=r".+_[0-9a-f]{8}\.(mp3|wav|m4a|flac)",
        )

        log_event(
            event_type=EVENT_REPORT_GENERATION,
            message=f"Report generated for call {call_id}: {report_path}",
            severity=SEVERITY_INFO,
            call_id=call_id,
        )

        return {
            "call_id": call_id,
            "call_status": call_status,
            "report_path": str(report_path),
            "supervisor_review_needed": state.get("supervisor_review_needed"),
        }
    except Exception as e:
        log_event(
            event_type=EVENT_REPORT_GENERATION,
            message=f"Report generation failed: {str(e)}",
            severity=SEVERITY_ERROR,
        )
        return {"error": str(e), "error_logged": True}


def error_node(state: PipelineState) -> dict:
    """Persist terminal failures/blocks and log the existing pipeline error."""
    call_status = (
        CALL_STATUS_BLOCKED if state.get("injection_detected") else CALL_STATUS_FAILED
    )
    message = state.get("error") or (
        "Pipeline blocked by prompt injection"
        if call_status == CALL_STATUS_BLOCKED
        else "Pipeline failed"
    )
    caller_id, department = _redact_metadata(state)
    call_id = state.get("call_id") or save_failed_call(
        audio_path=state.get("audio_path"),
        file_hash=state.get("file_hash"),
        error=message,
        status=call_status,
        transcript=state.get("transcript"),
        duration=state.get("duration"),
        speaker_count=state.get("speaker_count"),
        segments=state.get("segments"),
        confidence=state.get("confidence"),
        caller_id=caller_id,
        department=department,
    )

    if not state.get("error_logged"):
        log_event(
            event_type=EVENT_PIPELINE,
            message=message,
            severity=SEVERITY_WARNING
            if call_status == CALL_STATUS_BLOCKED
            else SEVERITY_ERROR,
            call_id=call_id,
        )

    return {"call_id": call_id, "call_status": call_status}


def supervisor_node(state: PipelineState) -> dict:
    """Flag the call for supervisor review."""
    log_event(
        event_type=EVENT_SUPERVISOR_REVIEW,
        message="Call needs supervisor review",
        severity=SEVERITY_WARNING,
        call_id=state.get("call_id"),
    )

    return {"supervisor_review_needed": True}
