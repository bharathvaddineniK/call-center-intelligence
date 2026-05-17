# Call Center Intelligence Specs

## Full Architecture With Data Flow

```text
Gradio UI
  |
  | audio filepath
  v
LangGraph StateGraph
  |
  +--> intake
  |      validates file path, format, size, and duration
  |
  +--> transcription
  |      SHA-256 hash -> transcription cache lookup
  |      Groq hosted transcription -> Groq fallback -> faster-whisper local fallback
  |      transcript cleanup -> heuristic speaker assignment
  |
  +--> injection_check
  |      regex prompt-injection detection
  |      detected injection routes to error and stops before LLM calls
  |
  +--> pii_redaction
  |      Presidio + regex fallback redaction
  |      transcript and segment text are redacted before LLM calls
  |
  +--> summarize_qa
  |      structured SummaryResult from configured LLM provider
  |      structured QAResult from configured LLM provider
  |      deterministic weighted overall score recomputation
  |
  +--> supervisor
  |      triggered when compliance flag and low score require review
  |      sets supervisor_review_needed and continues to report
  |
  +--> report
         persists call/report rows
         writes JSON and PDF reports
         runs copied-audio cleanup
```

Every pipeline event writes append-only rows to `audit_log`. The Observability UI reads metrics and
audit rows directly from SQLite.

## Design Decisions And Tradeoffs

- **LangGraph orchestration:** The pipeline uses a compiled `StateGraph` to make branching explicit
  and reusable across UI requests.
- **Separate report persistence:** Reports live in a dedicated `reports` table rather than inside
  `call_records`. This keeps raw call metadata separate from generated analysis outputs.
- **Transcription cache:** Audio content is hashed with SHA-256, so repeated uploads of identical
  audio can reuse cached transcription results.
- **LLM provider factory:** OpenAI, Gemini, and Groq are switchable through `LLM_PROVIDER`.
- **Deterministic QA overall score:** The LLM returns dimension scores, but the final overall score
  is recomputed from fixed weights in code.
- **PII redaction fallback:** Regex fallback uses `re.subn` for supported non-overlapping formats.
  This is simpler than offset-based right-to-left replacement while preserving behavior for the
  current PII patterns.
- **UI copied-upload cleanup:** The report stage cleans only UUID-suffixed copied uploads, preserving
  stable sample files used by tests.

## API Contracts Between Pipeline Stages

All stages read and return partial updates to `PipelineState`.

### `intake`

Input:

- `audio_path: str`

Output:

- `duration: float`
- or `error: str`

### `transcription`

Input:

- `audio_path`

Output:

- `file_hash: str`
- `transcript: str`
- `segments: list[dict]`
- `confidence: float`
- `speaker_count: int`
- or `error: str`

### `injection_check`

Input:

- `transcript`

Output:

- `injection_detected: bool`
- or `error: str`

Routing:

- `True` routes to `error`
- `False` routes to `pii_redaction`

### `pii_redaction`

Input:

- `transcript`
- `segments`

Output:

- redacted `transcript`
- redacted `segments`
- `pii_detected: bool`
- or `error: str`

### `summarize_qa`

Input:

- redacted `transcript`

Output:

- `summary: str`
- `sentiment: str`
- `agent_behavior: str`
- `call_purpose: str`
- `qa_scores: dict[str, float]`
- `overall_score: float`
- `compliance_flag: bool`
- `summary_json: str`
- or `error: str`

Routing:

- compliance flag plus score below threshold routes to `supervisor`
- otherwise routes to `report`

### `supervisor`

Input:

- QA state fields

Output:

- `supervisor_review_needed: bool`

Routing:

- continues to `report`

### `report`

Input:

- all upstream call, summary, QA, and report fields

Output:

- `call_id: int`
- `report_path: str`
- `supervisor_review_needed: bool | None`
- or `error: str`

### `error`

Input:

- `error: str`
- optional `call_id`

Output:

- empty update after audit logging

## Security Implementation Notes

- Prompt injection is checked immediately after transcription and before PII redaction or LLM calls.
- Injection detection uses regex categories for instruction override, role manipulation, system
  prompt leakage, jailbreak, score manipulation, and data exfiltration.
- PII redaction runs before summarization and QA scoring.
- PII coverage includes phone numbers, email addresses, US SSNs, and credit cards.
- Presidio handles entity analysis/anonymization, with regex fallback for common variants.
- Audit logging is append-only and validates event types and severities.
- `.env` is excluded from Docker build context by `.dockerignore`.
- LangSmith dashboard status is visible in Observability when tracing is configured.

## Known Limitations

- Diarization is heuristic and labels alternating speakers as `Agent` and `Customer`; it is not a
  trained speaker-identification model.
- QA timestamp references are requested in the prompt but are not structurally enforced in the
  `QAResult` schema.
- Unit tests marked `integration` call real LLM APIs when included in a full local test run.
- Dockerfile is CPU-oriented. GPU deployments should use a CUDA-enabled base image.
- SQLite is appropriate for local/capstone use but should be replaced or migrated for high-volume
  multi-user production deployments.
- LangSmith project dashboard URLs include organization/project IDs, so the URL is configured with
  `LANGSMITH_PROJECT_URL` rather than derived from the project name.
