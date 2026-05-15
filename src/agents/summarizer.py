"""Summarize call transcripts into structured call-center analytics."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import traceable

import config
from src.pipeline_models import SummaryResult


SYSTEM_PROMPT = """You are a call center analyst. Analyze only the given transcript.

Return the following fields:
1. Summary: Summarize the conversation in 2-3 sentences.
2. Intent: Identify the caller's purpose.
3. Agent behavior: Describe how the agent responded to the caller.
4. Key entities: List important people, places, products, or topics mentioned.
5. Sentiment: Classify the overall emotional tone as positive, negative, or neutral.

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

LLM = ChatOpenAI(
    api_key=config.OPENAI_API_KEY,
    model=config.LLM_MODEL,
)

STRUCTURED_LLM = LLM.with_structured_output(SummaryResult)
SUMMARY_CHAIN = SUMMARY_PROMPT | STRUCTURED_LLM


@traceable
def summarize(transcript_text: str) -> SummaryResult:
    """Analyze a transcript and return structured summary fields."""
    return SUMMARY_CHAIN.invoke({"transcript": transcript_text})
