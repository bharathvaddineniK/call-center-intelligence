"""Score call transcripts for quality assurance metrics."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import traceable
from src.pipeline_models import QAResult
import config

LLM = ChatOpenAI(
    api_key=config.OPENAI_API_KEY,
    model=config.LLM_MODEL,
    temperature=0
)

SYSTEM_PROMPT = """You are a call center quality analyst. Analyze only the given transcript.

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
"""

HUMAN_PROMPT = "Analyse the transcript:\n\n{transcript}"

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_PROMPT)
])

STRUCTURED_LLM = LLM.with_structured_output(QAResult)
QA_CHAIN = QA_PROMPT | STRUCTURED_LLM

@traceable
def score(transcript_text: str) -> QAResult:
    """Analyze a transcript and return structured QA scores."""
    result = QA_CHAIN.invoke({"transcript": transcript_text})
    result.overall_score = _recompute_overall_score(result)

    return result

def _recompute_overall_score(result: QAResult) -> float:
    """Calculate the weighted overall QA score from individual category scores."""
    overall_score = (
        result.empathy_score * 0.25 +
        result.resolution_score * 0.30 +
        result.compliance_score * 0.20 +
        result.communication_score * 0.15 +
        result.professionalism_score * 0.10
    ) 

    return round(overall_score,2)
