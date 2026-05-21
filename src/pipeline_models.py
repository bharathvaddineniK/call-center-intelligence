from datetime import datetime
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class PipelineState(TypedDict):
    audio_path: str
    caller_id: str | None
    department: str | None
    file_hash: str | None
    duration: float | None
    transcript: str | None
    segments: list[dict[str, Any]] | None
    confidence: float | None
    low_quality_audio: bool | None
    speaker_count: int | None
    pii_detected: bool | None
    injection_detected: bool | None
    injection_patterns: list[str] | None
    sentiment: str | None
    call_purpose: str | None
    agent_behavior: str | None
    qa_scores: dict[str, float] | None
    overall_score: float | None
    compliance_flag: bool | None
    compliance_severity: str | None
    violation_description: str | None
    timestamp_evidence: list[str] | None
    summary: str | None
    call_id: int | None
    call_status: str | None
    report_path: str | None
    error: str | None
    error_logged: bool | None
    supervisor_review_needed: bool | None
    audit_events: list[dict[str, Any]] | None
    summary_json: str | None
    token_usage: dict[str, Any] | None


class TranscriptionSegment(BaseModel):
    start: float = Field(description="Start time of the segment in seconds")
    end: float = Field(description="End time of the segment in seconds")
    text: str = Field(description="Transcribed text for this segment")
    speaker: str | None = Field(None, description="Speaker ID if available")
    confidence: float | None = Field(None, description="Confidence score of the transcription")


class SpeakerSegment(BaseModel):
    start: float = Field(description="Start time of the speaker segment in seconds")
    end: float = Field(description="End time of the speaker segment in seconds")
    text: str = Field(description="Transcript text for this speaker segment")
    speaker: str | None = Field(None, description="Assigned speaker role or ID")
    confidence: float | None = Field(None, description="Confidence score for this segment")


class ValidationResult(BaseModel):
    is_valid: bool = Field(description="Whether the audio file passed intake validation")
    error: str | None = Field(None, description="Validation failure reason, if any")
    duration: float | None = Field(None, description="Audio duration in seconds")
    file_size_mb: float | None = Field(None, description="Audio file size in megabytes")


class TranscriptionResult(BaseModel):
    text: str = Field(description="Full cleaned transcript text")
    segments: list[dict[str, Any]] = Field(description="Timestamped transcript segments")
    confidence: float = Field(description="Overall transcription confidence")
    speaker_count: int = Field(description="Number of detected speakers")
    source: str = Field(description="Transcription source, such as cache, Groq, or Whisper")
    duration: float = Field(description="Audio duration in seconds")
    file_hash: str = Field(default="", description="Content hash used for transcript cache lookup")


class ComplianceFlag(BaseModel):
    severity: Literal["none", "low", "medium", "high", "critical"] = Field(
        description="Severity of the compliance issue"
    )
    description: str = Field(description="Compliance finding or violation description")
    timestamp_reference: str | None = Field(
        None,
        description="Transcript timestamp supporting the compliance finding",
    )


class PipelineError(BaseModel):
    node_name: str = Field(description="Pipeline node where the error occurred")
    message: str = Field(description="Error message")
    timestamp: datetime = Field(description="Time the error was recorded")


class AudioMetadata(BaseModel):
    filename: str = Field(description="Audio filename")
    duration: float | None = Field(None, description="Audio duration in seconds")
    size_mb: float | None = Field(None, description="Audio file size in megabytes")
    format: str = Field(description="Detected audio format")


class SummaryResult(BaseModel):
    summary: str = Field(description="Text summary of the call")
    sentiment: str = Field(description="Overall sentiment: positive/negative/neutral")
    agent_behavior: str = Field(description="How the agent handled the call")
    key_entities: list[str] = Field(description="List of key entities extracted from the call")
    call_purpose: str = Field(description="The purpose of the call")
    key_discussion_points: list[str] = Field(description="List of 3 to 7 key points discussed")
    action_items: list[str] = Field(
        description="List of actions to be taken and the respective owner"
    )
    resolution_status: Literal["resolved", "unresolved", "escalated"] = Field(
        description="Resolution of the call"
    )
    sentiment_trajectory: str = Field(
        description="What's the trajectory of sentiment e.g: Frustrated → Satisfied"
    )


class QAResult(BaseModel):
    empathy_score: float = Field(ge=1, le=5, description="1-5 score for agent empathy")
    resolution_score: float = Field(
        ge=1,
        le=5,
        description="1-5 score for issue resolution effectiveness",
    )
    compliance_score: float = Field(ge=1, le=5, description="1-5 score for policy compliance")
    communication_score: float = Field(
        ge=1,
        le=5,
        description="1-5 score for communication clarity",
    )
    professionalism_score: float = Field(ge=1, le=5, description="1-5 score for conduct")
    overall_score: float = Field(ge=1, le=5, description="Overall 1-5 QA score")
    compliance_flag: bool = Field(description="Whether the call complies with standards")
    compliance_severity: Literal["none", "low", "medium", "high", "critical"] = Field(
        description="Severity of the compliance issue, or none when no issue exists"
    )
    violation_description: str = Field(
        description="Specific compliance violation, or 'No violation detected'"
    )
    timestamp_evidence: list[str] = Field(
        description="Transcript timestamps supporting the compliance decision"
    )
    reasoning: str = Field(description="Explanation for the scores and flag")


class CallReportCall(BaseModel):
    id: int | str = Field(description="Database call id")
    filename: str = Field(description="Original audio filename")
    duration: float | str = Field(description="Call duration in seconds")
    speaker_count: int | str = Field(description="Number of detected speakers")
    sentiment: str = Field(description="Overall call sentiment")
    call_purpose: str = Field(description="The purpose of the call")
    agent_behavior: str = Field(description="How the agent handled the call")


class CallReportSummary(BaseModel):
    summary: str = Field(description="Text summary of the call")
    agent_behavior: str = Field(description="How the agent handled the call")
    key_entities: list[str] = Field(description="Key entities extracted from the call")
    key_discussion_points: list[str] = Field(description="Important discussion points")
    action_items: list[str] = Field(description="Actions to be taken")
    resolution_status: str = Field(description="Resolution status")
    sentiment_trajectory: str = Field(description="Sentiment trajectory over the call")


class CallReportQA(BaseModel):
    overall_score: float | str = Field(description="Overall QA score")
    empathy_score: float | str = Field(description="Empathy score")
    resolution_score: float | str = Field(description="Resolution score")
    compliance_score: float | str = Field(description="Compliance score")
    communication_score: float | str = Field(description="Communication score")
    professionalism_score: float | str = Field(description="Professionalism score")
    compliance_flag: bool | str = Field(description="Whether compliance issues were detected")
    compliance_severity: str = Field(description="Compliance severity")
    violation_description: str = Field(description="Compliance violation description")
    timestamp_evidence: list[str] = Field(description="Timestamped evidence")


class CallReport(BaseModel):
    call: CallReportCall
    summary: CallReportSummary
    qa: CallReportQA
