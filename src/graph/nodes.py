from pathlib import Path
from types import SimpleNamespace

import config
from src.pipeline_models import PipelineState, SummaryResult
from src.services.audio.validator import validate_audio
from src.services.audio.transcriber import get_transcription
from src.services.audio.diarization import assign_speakers
from src.services.security.audit_logger import (
    log_event,
    EVENT_PIPELINE_STARTED,
    EVENT_PIPELINE_FAILED,
    EVENT_TRANSCRIPTION_COMPLETE,
    EVENT_INJECTION_DETECTED,
    EVENT_PII_DETECTED,
    EVENT_ANALYSIS_COMPLETE,
    EVENT_REPORT_GENERATED,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
)
from src.services.security.injection_detector import detect_injection
from src.services.security.pii_redactor import redact_pii
from src.services.reports.generator import generate_json, generate_pdf
from src.agents.summarizer import summarize
from src.agents.qa_scorer import score
from src.database.repository import save_call, save_report, get_call_by_hash

def intake_node(state: PipelineState) -> dict:
    """Validates the audio and returns the duration of the audio"""
    try:
        audio_path = state["audio_path"]
        result = validate_audio(audio_path)
        
        if not result.is_valid:
            log_event(
                event_type=EVENT_PIPELINE_FAILED, 
                message=f"Intake failed: {result.error}", 
                severity=SEVERITY_ERROR
            )
            return {"error": result.error}
        
        log_event(
            event_type=EVENT_PIPELINE_STARTED, 
            message=f"Intake validated: {audio_path}", 
            severity=SEVERITY_INFO
        )
        
        return {
            "duration": result.duration
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PIPELINE_FAILED, 
            message=str(e), 
            severity=SEVERITY_ERROR
        )
        return {"error": str(e)}
    
def transcription_node(state: PipelineState) -> dict:
    try:
        audio_path = state["audio_path"]
        result = get_transcription(audio_path)
        segments_with_speakers = assign_speakers(result.segments)

        log_event(
            event_type=EVENT_TRANSCRIPTION_COMPLETE,
            message=f"Transcribed via {result.source} with confidence of {result.confidence}",
            severity=SEVERITY_INFO
        )

        return {
            "file_hash": result.file_hash,
            "transcript":result.text, 
            "segments":segments_with_speakers,
            "confidence": result.confidence,
            "speaker_count": len(set(s.get("speaker") for s in segments_with_speakers if s.get("speaker"))),
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PIPELINE_FAILED, 
            message=str(e), 
            severity=SEVERITY_ERROR
        )
        return {"error": f"Transcription failed: {str(e)}"}
    
def injection_check_node(state: PipelineState) -> dict:
    """Checks the audio transcription for any prompt injection"""

    try:
        if detect_injection(state['transcript']):
            log_event(
                event_type=EVENT_INJECTION_DETECTED,
                message="Injection detected",
                severity=SEVERITY_WARNING
            )

            return {
                "injection_detected": True
            }
        
        log_event(
            event_type=EVENT_ANALYSIS_COMPLETE,
            message="No injection detected",
            severity=SEVERITY_INFO
        )

        return {
            "injection_detected": False
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PIPELINE_FAILED,
            message=str(e),
            severity=SEVERITY_ERROR
        )
        return {"error": str(e)}

def pii_redaction_node(state: PipelineState) -> dict:
    """Reacts the PII with placeholders"""

    try:
        redacted_text, pii_detected = redact_pii(state["transcript"])

        redacted_segments = []

        for segment in state["segments"]:
            redacted_segment_text, _ = redact_pii(segment["text"])
            redacted_segments.append({**segment, "text": redacted_segment_text})
        
        if pii_detected:
            log_event(event_type=EVENT_PII_DETECTED, message="PII redacted", severity=SEVERITY_WARNING)
        else:
            log_event(event_type=EVENT_ANALYSIS_COMPLETE, message="No PII detected", severity=SEVERITY_INFO)

        return {
            "transcript": redacted_text,
            "segments": redacted_segments,
            "pii_detected": pii_detected
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PIPELINE_FAILED,
            message=str(e),
            severity=SEVERITY_ERROR
        )
        return {"error": str(e)}
    
def summarize_qa_node(state: PipelineState) -> dict:
    """Summarize the transcript and return summary and QA state fields."""

    try:
        transcript = state["transcript"]
        summary = summarize(transcript)

        log_event(
            event_type=EVENT_ANALYSIS_COMPLETE,
            message="Summary generated",
            severity=SEVERITY_INFO,
        )

        qa_score = score(transcript, summary)

        log_event(
            event_type=EVENT_ANALYSIS_COMPLETE,
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
            "summary_json": summary.model_dump_json()
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PIPELINE_FAILED,
            message=f"Summary or QA failed: {str(e)}",
            severity=SEVERITY_ERROR,
        )
        return {"error": str(e)}
    
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

        audio_path = state["audio_path"]
        filename = Path(audio_path).name

        existing_call = get_call_by_hash(file_hash)
        if existing_call:
            call_id = existing_call.id
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
                segments=segments,
                confidence=confidence,
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

        log_event(
            event_type=EVENT_REPORT_GENERATED,
            message=f"Report generated for call {call_id}: {report_path}",
            severity=SEVERITY_INFO,
            call_id=call_id,
        )

        return {
            "call_id": call_id,
            "report_path": str(report_path),
        }
    except Exception as e:
        log_event(
            event_type=EVENT_PIPELINE_FAILED,
            message=f"Report generation failed: {str(e)}",
            severity=SEVERITY_ERROR,
        )
        return {"error": str(e)}


def error_node(state: PipelineState) -> dict:
    """Log the existing pipeline error and return an empty update."""
    log_event(
        event_type=EVENT_PIPELINE_FAILED,
        message=state.get("error", "Pipeline failed"),
        severity=SEVERITY_ERROR,
        call_id=state.get("call_id"),
    )

    return {}


def supervisor_node(state: PipelineState) -> dict:
    """Flag the call for supervisor review."""
    log_event(
        event_type=EVENT_ANALYSIS_COMPLETE,
        message="Call needs supervisor review",
        severity=SEVERITY_WARNING,
        call_id=state.get("call_id"),
    )

    return {"supervisor_review_needed": True}
