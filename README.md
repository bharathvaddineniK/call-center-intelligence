---
title: Call Center Intelligence
sdk: docker
app_port: 7860
pinned: false
---

# Call Center Intelligence

## Live Demo

[https://bkumarvaddineni-call-center-intelligence.hf.space](https://bkumarvaddineni-call-center-intelligence.hf.space)

Call Center Intelligence is a LangGraph-based operations console for analyzing support and
emergency-style call audio. It validates and transcribes audio, blocks prompt-injection attempts,
redacts PII, summarizes the call, scores agent quality, persists call history, writes audit
records, and produces downloadable PDF and JSON reports through a Gradio UI.

## Architecture Overview

The project is organized into six main layers:

- `src/ui`: Gradio application for upload, analysis, report downloads, and observability.
- `src/graph`: LangGraph `StateGraph` orchestration and pipeline routing.
- `src/services`: audio validation/transcription/cleanup, security checks, and report generation.
- `src/agents`: LLM provider factory, structured summarization, and QA scoring.
- `src/database`: SQLAlchemy models, repository helpers, and session management.
- `src/pipeline_models.py`: shared typed models for pipeline state, audio metadata, transcript
  results, summary/QA outputs, report payloads, compliance flags, and structured errors.

The pipeline stages are:

1. `intake`: validate file existence, supported format, 50 MB size limit, and 60 minute duration
   limit.
2. `transcription`: transcribe with Groq, fall back to Groq Turbo and local faster-whisper, assign
   speaker labels, cache transcripts by SHA-256 hash, and flag low-quality audio by confidence.
3. `injection_check`: stop malicious prompt-injection transcripts before LLM calls and record
   matched injection pattern names.
4. `pii_redaction`: redact SSN, credit card, email, and phone values before LLM calls.
5. `summarize_qa`: generate a full structured summary and 1-5 QA scorecard with token usage.
6. `supervisor`: route critical compliance severity calls for supervisor review.
7. `report`: persist call/report data and generate PDF/JSON artifacts.
8. `error`: persist failed or blocked calls with minimal records and audit details.

The graph stores terminal calls with one of four statuses: `completed`, `flagged`, `blocked`, or
`failed`. Completed and flagged calls include reports; blocked and failed calls are still visible in
observability because the error path persists a minimal call record.

## UI Capabilities

- `Analyze Call`: upload audio, optionally provide caller ID and department metadata, run the full
  pipeline, inspect speaker-bubble conversation view, transcript, summary, QA scorecard, token
  usage, processing status, and PDF/JSON report downloads.
- `MP3 History`: review previously analyzed MP3 calls from the database and reload their transcript,
  summary, QA scorecard, and stored report downloads without rerunning analysis.
- `Observability`: inspect call status counts, success rate, average QA score, compliance flags,
  storage diagnostics, LangSmith trace link, audit events, and CSV audit export.

## Setup Instructions

Create and activate a Python 3.11 environment:

```bash
python3.11 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
make install
```

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Fill in the provider keys you plan to use. At minimum, set the API key for `LLM_PROVIDER`.

Common environment variables:

- `LLM_PROVIDER`: `openai`, `gemini`, or `groq`.
- `OPENAI_MODEL`, `GEMINI_MODEL`, `GROQ_LLM_MODEL`: model IDs for summary and QA scoring.
- `GROQ_API_KEY`: required for hosted audio transcription.
- `MIN_CONFIDENCE_THRESHOLD`: transcript confidence threshold for low-quality audio warnings.
- `GRADIO_SERVER_PORT`: optional explicit Gradio port.
- `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_PROJECT_URL`: optional tracing setup.

## How To Run Locally

Start the Gradio app:

```bash
make run
```

Open the local URL printed by Gradio, usually:

```text
http://127.0.0.1:7860
```

The root `app.py` initializes the SQLite database, preloads the local faster-whisper fallback model,
and launches the UI.

## How To Run Tests

Run CI-safe tests that do not require real external API calls:

```bash
make test
```

Run only integration-marked tests that may require real API keys:

```bash
make test-integration
```

Run the full suite locally:

```bash
make test-all
```

Run Ruff linting and formatting:

```bash
make lint
make format
```

## Quality And Security Controls

- Audio intake accepts `.mp3`, `.wav`, `.m4a`, and `.flac` and rejects files over 50 MB or 60
  minutes.
- WAV duration is read from the RIFF header before size-based rejection so long WAV files surface
  the rubric-required duration error.
- Transcript cache is reused only for transcription. Summary, QA scoring, compliance routing, and
  reports are regenerated on each analysis so scores use the latest prompts and logic.
- Prompt-injection detection blocks analysis before LLM calls and stores matched pattern names in
  state and UI/audit messages.
- PII redaction scans transcript text, transcript segments, caller ID, and department metadata
  before storage or LLM use.
- Low-quality audio is flagged when transcription confidence falls below
  `MIN_CONFIDENCE_THRESHOLD`.
- Supervisor routing is based on explicit `compliance_severity == "critical"` rather than a proxy
  of boolean compliance flag plus low score.

## GPU And Startup Notes

The local faster-whisper fallback is preloaded at app startup through
`preload_whisper_model()`. It auto-detects CUDA; if CUDA is available, it uses GPU execution with
`float16`, otherwise it falls back to CPU with `int8`.

For GPU deployment:

- Use a CUDA-enabled base image and install a CUDA-compatible PyTorch build.
- Mount or persist Hugging Face/model caches to avoid repeated model downloads.
- Ensure `ffmpeg` and `libsndfile` are available in the runtime image.
- Keep `BEAM_SIZE=1` for lower latency unless accuracy requirements justify a larger beam.

The provided Dockerfile uses `python:3.11-slim` and is CPU-oriented.

## Docker Persistence

Runtime state is stored under `/app/data` in the container, including SQLite observability data,
reports, uploaded audio copies, and the transcription cache. Mount that directory as a volume when
running Docker; otherwise, recreating the container starts with a fresh database and observability
will show zero historical stats.

```bash
docker run --env-file .env -p 7860:7860 -v call-center-data:/app/data call-center-intelligence
```

If port `7860` is already allocated, stop the existing container or map a different host port:

```bash
docker run --env-file .env -p 7861:7860 -v call-center-data:/app/data call-center-intelligence
```

## Sample Usage / Screenshots

Analyze a call:

1. Open the `Analyze Call` tab.
2. Upload an `.mp3`, `.wav`, `.m4a`, or `.flac` file.
3. Optionally enter caller ID and department metadata.
4. Click `Analyze Call`.
5. Watch the current pipeline step and progress percentage.
6. Review the speaker transcript, summary, QA scorecard, token usage, and downloads.

History:

1. Open the `MP3 History` tab.
2. Select a stored MP3 call.
3. Review the persisted analysis and download stored reports.

Observability:

1. Open the `Observability` tab.
2. Review status counts, success rate, average QA score, compliance flags, storage diagnostics, and
   LangSmith status.
3. Scroll the audit table to inspect pipeline events.
4. Click `Export Audit Log` to reveal a CSV download button.

## Report Contents

Generated reports include:

- Call metadata, transcript, speaker segments, confidence, and low-quality audio indicator.
- Summary, sentiment, call purpose, agent behavior, key entities, key discussion points, action
  items, resolution status, and sentiment trajectory.
- QA scores on a 1-5 scale for empathy, resolution, compliance, communication, professionalism, and
  overall performance.
- Compliance severity, violation description, timestamp evidence, and supervisor-review flag.
- Token usage for summary and QA scoring when provider usage metadata is available.

## Implementation Notes

- PII redaction uses Presidio plus deterministic regex fallbacks.
- Speaker assignment uses transcript timing plus call-center and emergency-call cue scoring. It is
  still heuristic diarization, not voice-embedding diarization.
- The database includes a separate `reports` table in addition to `call_records`, `audit_log`, and
  `transcription_cache`. Keeping reports separate preserves a cleaner call/report boundary. Full
  generated report JSON is also stored in `reports.report_json` for history reloads.
- SQLAlchemy uses a module-level `sessionmaker` and a `session_scope` context manager for
  commit/rollback handling.
- Existing SQLite databases are migrated at startup with additive column checks for status,
  metadata, report JSON, and compliance fields.
- User-specific persistence is not implemented yet. A shared deployment with one mounted `/app/data`
  volume shows shared history and observability to all visitors unless an authentication/user
  partition layer is added.
