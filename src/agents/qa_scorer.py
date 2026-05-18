"""Score call transcripts for quality assurance metrics."""

from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.agents.llm_factory import get_fallback_llm, get_llm
from src.agents.retry import is_model_access_error, is_retryable_llm_error
from src.pipeline_models import QAResult, SummaryResult

SUMMARY_JSON_INDENT = 2
RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 2
RETRY_MAX_WAIT_SECONDS = 10

SCORE_WEIGHTS = (
    ("empathy_score", 0.20),
    ("resolution_score", 0.30),
    ("compliance_score", 0.20),
    ("communication_score", 0.15),
    ("professionalism_score", 0.15),
)

LLM = get_llm(temperature=0)

SYSTEM_PROMPT = """You are a call center quality analyst.
Analyze only the given transcript and summary.

Return the following fields:
1. empathy_score: score for agent's empathy level.
2. resolution_score: score for issue resolution effectiveness.
3. compliance_score: score for compliance with policies.
4. communication_score: score for communication clarity.
5. professionalism_score: score for professional conduct.
6. compliance_flag: whether the call complies with standards.
7. reasoning: explanation for the scores and flag.

SCORING SCALE: All scores must be between 0 and 100, where:
- 0-20: Very poor
- 21-40: Poor  
- 41-60: Average
- 61-80: Good
- 81-100: Excellent

Hard rules:
1. Use only information present in the transcript.
2. Do not infer or assume missing details.
3. When writing reasoning, reference specific transcript timestamps where possible.
For example: "At 02:15, the agent failed to verify identity".
"""

HUMAN_PROMPT = "Analyse the Transcript:\n\n{transcript}\n\nCall Summary:\n\n{summary}"

QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
    ]
)

STRUCTURED_LLM = LLM.with_structured_output(QAResult)
QA_CHAIN = QA_PROMPT | STRUCTURED_LLM
FALLBACK_QA_CHAIN = None
LAST_QA_USAGE = {}


@traceable
def score(transcript_text: str, summary: SummaryResult) -> QAResult:
    """Analyze a transcript and return structured QA scores."""
    result, _usage = score_with_usage(transcript_text, summary)
    return result


@traceable
def score_with_usage(transcript_text: str, summary: SummaryResult) -> tuple[QAResult, dict]:
    """Analyze a transcript and return QA scores plus provider token usage."""
    inputs = _build_score_inputs(transcript_text, summary)
    try:
        result, usage = _invoke_with_retry(QA_CHAIN, inputs)
    except Exception as exc:
        if not is_model_access_error(exc):
            raise
        result, usage = _invoke_with_retry(_get_fallback_qa_chain(), inputs)

    result.overall_score = _recompute_overall_score(result)

    return result, usage


def _build_score_inputs(transcript_text: str, summary: SummaryResult) -> dict:
    """Build the prompt variables passed into the QA scoring chain."""
    return {
        "transcript": transcript_text,
        "summary": summary.model_dump_json(indent=SUMMARY_JSON_INDENT),
    }


def _get_fallback_qa_chain():
    """Build the fallback QA chain only if the primary model is unavailable."""
    global FALLBACK_QA_CHAIN

    if FALLBACK_QA_CHAIN is None:
        fallback_llm = get_fallback_llm(temperature=0)
        FALLBACK_QA_CHAIN = QA_PROMPT | fallback_llm.with_structured_output(QAResult)

    return FALLBACK_QA_CHAIN


def get_last_qa_usage() -> dict:
    """Return token usage from the most recent QA call."""
    return LAST_QA_USAGE.copy()


def _summarize_usage(usage_metadata: dict) -> dict:
    """Flatten provider usage metadata across models."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "models": [],
        "source": "actual",
    }
    for model_name, usage in usage_metadata.items():
        totals["models"].append(model_name)
        totals["input_tokens"] += int(usage.get("input_tokens", 0) or 0)
        totals["output_tokens"] += int(usage.get("output_tokens", 0) or 0)
        totals["total_tokens"] += int(usage.get("total_tokens", 0) or 0)

    return totals


def _recompute_overall_score(result: QAResult) -> float:
    """Calculate the weighted overall QA score from individual category scores."""
    overall_score = sum(
        getattr(result, score_field) * weight
        for score_field, weight in SCORE_WEIGHTS
    )

    return round(overall_score, 2)


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(
        multiplier=1,
        min=RETRY_MIN_WAIT_SECONDS,
        max=RETRY_MAX_WAIT_SECONDS,
    ),
    retry=retry_if_exception(is_retryable_llm_error),
    reraise=True,
)
def _invoke_with_retry(chain, inputs):
    """Invoke a LangChain chain with retry handling for transient failures."""
    global LAST_QA_USAGE

    with get_usage_metadata_callback() as callback:
        result = chain.invoke(inputs)

    LAST_QA_USAGE = _summarize_usage(callback.usage_metadata)
    return result, LAST_QA_USAGE
