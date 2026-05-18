"""Summarize call transcripts into structured call-center analytics."""

from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.agents.llm_factory import get_fallback_llm, get_llm
from src.agents.retry import is_model_access_error, is_retryable_llm_error
from src.pipeline_models import SummaryResult

LLM_TEMPERATURE = 0
RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 2
RETRY_MAX_WAIT_SECONDS = 10

SYSTEM_PROMPT = """You are a call center analyst. Analyze only the given transcript.

Return the following fields:
1. Summary: Summarize the conversation in 2-3 sentences.
2. Call purpose: Identify the caller's purpose.
3. Agent behavior: Describe how the agent responded to the caller.
4. Key entities: List important people, places, products, or topics mentioned.
5. Sentiment: Classify the overall emotional tone as positive, negative, or neutral.
6. Key discussion points: List of 3 to 7 key points discussed.
7. Action items: List of actions to be taken and the respective owner 
8. Resolution Status: Resolution of the call (resolved/unresolved/escalated)
9. Sentiment Trajectory: What's the trajectory of sentiment e.g: Frustrated → Satisfied


Hard rules:
1. Use only information present in the transcript.
2. Do not infer or assume missing details.
"""

HUMAN_PROMPT = "Analyze the transcript:\n\n{transcript}"

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
    ]
)

LLM = get_llm(temperature=LLM_TEMPERATURE)

STRUCTURED_LLM = LLM.with_structured_output(SummaryResult)
SUMMARY_CHAIN = SUMMARY_PROMPT | STRUCTURED_LLM
FALLBACK_SUMMARY_CHAIN = None
LAST_SUMMARY_USAGE = {}


@traceable
def summarize(transcript_text: str) -> SummaryResult:
    """Analyze a transcript and return structured summary fields."""
    result, _usage = summarize_with_usage(transcript_text)
    return result


@traceable
def summarize_with_usage(transcript_text: str) -> tuple[SummaryResult, dict]:
    """Analyze a transcript and return summary fields plus provider token usage."""
    inputs = _build_summary_inputs(transcript_text)
    try:
        return _invoke_with_retry(SUMMARY_CHAIN, inputs)
    except Exception as exc:
        if is_model_access_error(exc):
            return _invoke_with_retry(_get_fallback_summary_chain(), inputs)
        raise


def _build_summary_inputs(transcript_text: str) -> dict:
    """Build the prompt variables passed into the summary chain."""
    return {"transcript": transcript_text}


def _get_fallback_summary_chain():
    """Build the fallback summary chain only if the primary model is unavailable."""
    global FALLBACK_SUMMARY_CHAIN

    if FALLBACK_SUMMARY_CHAIN is None:
        fallback_llm = get_fallback_llm(temperature=LLM_TEMPERATURE)
        FALLBACK_SUMMARY_CHAIN = SUMMARY_PROMPT | fallback_llm.with_structured_output(
            SummaryResult
        )

    return FALLBACK_SUMMARY_CHAIN


def get_last_summary_usage() -> dict:
    """Return token usage from the most recent summary call."""
    return LAST_SUMMARY_USAGE.copy()


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
    global LAST_SUMMARY_USAGE

    with get_usage_metadata_callback() as callback:
        result = chain.invoke(inputs)

    LAST_SUMMARY_USAGE = _summarize_usage(callback.usage_metadata)
    return result, LAST_SUMMARY_USAGE
