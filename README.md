# Call Center Intelligence

Call Center Intelligence is a LangGraph-based pipeline for analyzing support-call audio. It
validates and transcribes audio, blocks prompt-injection attempts, redacts PII, summarizes the
call, scores agent quality, writes audit records, and produces downloadable PDF and JSON reports
through a Gradio UI.

## Architecture Overview

The project is organized into five main layers under `src/`:

- `src/ui`: Gradio application for upload, analysis, report downloads, and observability.
- `src/graph`: LangGraph `StateGraph` orchestration and pipeline routing.
- `src/services`: audio validation/transcription/cleanup, security checks, and report generation.
- `src/agents`: LLM provider factory, structured summarization, and QA scoring.
- `src/database`: SQLAlchemy models, repository helpers, and session management.

The pipeline stages are:

1. `intake`: validate file existence, supported format, size, and duration.
2. `transcription`: transcribe with Groq/faster-whisper fallback and cache by SHA-256 hash.
3. `injection_check`: stop malicious prompt-injection transcripts before LLM calls.
4. `pii_redaction`: redact SSN, credit card, email, and phone values before LLM calls.
5. `summarize_qa`: generate structured summary and deterministic weighted QA score.
6. `supervisor`: flag low-score compliance calls for review.
7. `report`: persist call/report data and generate PDF/JSON artifacts.
8. `error`: isolate and log node failures without cascading exceptions.

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

## How To Run Locally

Start the Gradio app:

```bash
make run
```

Open the local URL printed by Gradio, usually:

```text
http://127.0.0.1:7860
```

The root `app.py` initializes the SQLite database and launches the UI.

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

## GPU Deployment Notes

The local faster-whisper fallback auto-detects CUDA. If CUDA is available, it uses GPU execution
with `float16`; otherwise it falls back to CPU with `int8`.

For GPU deployment:

- Use a CUDA-enabled base image and install a CUDA-compatible PyTorch build.
- Mount or persist Hugging Face/model caches to avoid repeated model downloads.
- Ensure `ffmpeg` and `libsndfile` are available in the runtime image.
- Keep `BEAM_SIZE=1` for lower latency unless accuracy requirements justify a larger beam.

The provided Dockerfile uses `python:3.11-slim` and is CPU-oriented.

## Sample Usage / Screenshots

Analyze a call:

1. Open the `Analyze call` tab.
2. Upload an `.mp3`, `.wav`, `.m4a`, or `.flac` file.
3. Click `Analyze`.
4. Wait for the processing message to complete.
5. Review transcript, summary, QA scorecard, and download PDF/JSON reports.

Observability:

1. Open the `Observability` tab.
2. Review total calls, success rate, average QA score, compliance flags, and LangSmith status.
3. Scroll the audit table to inspect pipeline events.
4. Click `Export Audit Log` to reveal a CSV download button.

Screenshots can be added under a future `docs/screenshots/` directory for final submission.

## Implementation Notes

- PII redaction uses Presidio plus deterministic regex fallbacks. The regex fallback uses `re.subn`
  for non-overlapping patterns, which is functionally equivalent to right-to-left replacement for
  the supported PII formats.
- The database includes a separate `reports` table in addition to `call_records`, `audit_log`, and
  `transcription_cache`. Keeping reports separate preserves a cleaner call/report boundary and
  avoids overloading call metadata rows.
- SQLAlchemy uses a module-level `sessionmaker` and a `session_scope` context manager for
  commit/rollback handling.
