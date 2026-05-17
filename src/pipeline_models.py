from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class PipelineState(TypedDict):
    audio_path: str
    file_hash: str | None
    duration: float | None
    transcript: str | None
    segments: list[dict[str, Any]] | None
    confidence: float | None
    speaker_count: int | None
    pii_detected: bool | None
    injection_detected: bool | None
    sentiment: str | None
    call_purpose: str | None
    agent_behavior: str | None
    qa_scores: dict[str, float] | None
    overall_score: float | None
    compliance_flag: bool | None
    summary: str | None
    call_id: int | None
    report_path: str | None
    error: str | None
    supervisor_review_needed: bool | None
    audit_events: list[dict[str, Any]] | None
    summary_json: str | None


class TranscriptionSegment(BaseModel):
    start: float = Field(description="Start time of the segment in seconds")
    end: float = Field(description="End time of the segment in seconds")
    text: str = Field(description="Transcribed text for this segment")
    speaker: str | None = Field(None, description="Speaker ID if available")
    confidence: float | None = Field(None, description="Confidence score of the transcription")


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
    empathy_score: float = Field(ge=0, le=100, description="Score for agent's empathy level")
    resolution_score: float = Field(
        ge=0,
        le=100,
        description="Score for issue resolution effectiveness",
    )
    compliance_score: float = Field(ge=0, le=100, description="Score for compliance with policies")
    communication_score: float = Field(ge=0, le=100, description="Score for communication clarity")
    professionalism_score: float = Field(ge=0, le=100, description="Score for professional conduct")
    overall_score: float = Field(ge=0, le=100, description="Overall QA score")
    compliance_flag: bool = Field(description="Whether the call complies with standards")
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


class CallReport(BaseModel):
    call: CallReportCall
    summary: CallReportSummary
    qa: CallReportQA
