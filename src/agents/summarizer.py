"""Summarize call transcripts into structured call-center analytics."""

from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.llm_factory import get_llm
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


@traceable
def summarize(transcript_text: str) -> SummaryResult:
    """Analyze a transcript and return structured summary fields."""
    return _invoke_with_retry(SUMMARY_CHAIN, _build_summary_inputs(transcript_text))


def _build_summary_inputs(transcript_text: str) -> dict:
    """Build the prompt variables passed into the summary chain."""
    return {"transcript": transcript_text}


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(
        multiplier=1,
        min=RETRY_MIN_WAIT_SECONDS,
        max=RETRY_MAX_WAIT_SECONDS,
    ),
)
def _invoke_with_retry(chain, inputs):
    """Invoke a LangChain chain with retry handling for transient failures."""
    return chain.invoke(inputs)
