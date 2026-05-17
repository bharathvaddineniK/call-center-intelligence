from typing import Optional, TypedDict, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class PipelineState(TypedDict):
    audio_path: str
    file_hash: Optional[str]
    duration: Optional[float]
    transcript: Optional[str]
    segments: Optional[List[Dict[str, Any]]]
    confidence: Optional[float] 
    speaker_count: Optional[int]
    pii_detected: Optional[bool]
    injection_detected: Optional[bool]
    sentiment: Optional[str]
    call_purpose: Optional[str]
    agent_behavior: Optional[str]
    qa_scores: Optional[Dict[str, float]]
    overall_score: Optional[float]
    compliance_flag: Optional[bool]
    summary: Optional[str]
    call_id: Optional[int]
    report_path: Optional[str]
    error: Optional[str]
    supervisor_review_needed: Optional[bool]
    audit_events: Optional[List[Dict[str, Any]]]
    summary_json: Optional[str]

class TranscriptionSegment(BaseModel):
    start: float = Field(description="Start time of the segment in seconds")
    end: float = Field(description="End time of the segment in seconds")
    text: str = Field(description="Transcribed text for this segment")
    speaker: Optional[str] = Field(None, description="Speaker ID if available")
    confidence: Optional[float] = Field(None, description="Confidence score of the transcription")

class SummaryResult(BaseModel):
    summary: str = Field(description="Text summary of the call")
    sentiment: str = Field(description="Overall sentiment: positive/negative/neutral")
    agent_behavior: str = Field(description="How the agent handled the call")
    key_entities: List[str] = Field(description="List of key entities extracted from the call")
    call_purpose: str = Field(description="The purpose of the call")
    key_discussion_points: list[str] = Field(description="List of 3 to 7 key points discussed")
    action_items: List[str] = Field(description="List of actions to be taken and the respective owner")
    resolution_status: Literal["resolved", "unresolved", "escalated"] = Field(description="Resolution of the call")
    sentiment_trajectory: str = Field(description="What's the trajectory of sentiment e.g: Frustrated → Satisfied")


class QAResult(BaseModel):
    empathy_score: float = Field(ge=0, le=100, description="Score for agent's empathy level")
    resolution_score: float = Field(ge=0, le=100, description="Score for issue resolution effectiveness")
    compliance_score: float = Field(ge=0, le=100, description="Score for compliance with policies")
    communication_score: float = Field(ge=0, le=100, description="Score for communication clarity")
    professionalism_score: float = Field(ge=0, le=100, description="Score for professional conduct")
    overall_score: float = Field(ge=0, le=100, description="Overall QA score")
    compliance_flag: bool = Field(description="Whether the call complies with standards")
    reasoning: str = Field(description="Explanation for the scores and flag")
