"""Build and route the call-center intelligence LangGraph pipeline."""

from langgraph.graph import END, StateGraph

from src.graph.nodes import (
    error_node,
    injection_check_node,
    intake_node,
    pii_redaction_node,
    report_node,
    summarize_qa_node,
    supervisor_node,
    transcription_node,
)
from src.pipeline_models import PipelineState


def get_graph():
    """Create and compile the call processing graph."""
    graph = StateGraph(PipelineState)
    graph.add_node("intake", intake_node)
    graph.add_node("transcription", transcription_node)
    graph.add_node("injection_check", injection_check_node)
    graph.add_node("pii_redaction", pii_redaction_node)
    graph.add_node("summarize_qa", summarize_qa_node)
    graph.add_node("report", report_node)
    graph.add_node("error", error_node)
    graph.add_node("supervisor", supervisor_node)

    graph.set_entry_point("intake")
    graph.add_conditional_edges(
        "intake",
        route_default,
        {
            "next_node": "transcription",
            "error": "error",
        },
    )

    graph.add_conditional_edges(
        "transcription",
        route_default,
        {
            "next_node": "injection_check",
            "error": "error",
        },
    )

    graph.add_conditional_edges(
        "injection_check",
        route_after_injection,
        {
            "next_node": "pii_redaction",
            "error": "error",
        },
    )

    graph.add_conditional_edges(
        "pii_redaction",
        route_default,
        {
            "next_node": "summarize_qa",
            "error": "error",
        },
    )

    graph.add_conditional_edges(
        "summarize_qa",
        route_after_qa,
        {
            "next_node": "report",
            "supervisor": "supervisor",
            "error": "error",
        },
    )

    graph.add_conditional_edges(
        "report",
        route_default,
        {
            "next_node": END,
            "error": "error",
        },
    )

    graph.add_edge("error", END)
    graph.add_edge("supervisor", "report")

    return graph.compile()


def route_default(state: PipelineState) -> str:
    """Simple error check for most nodes."""
    return "error" if state.get("error") else "next_node"


def route_after_injection(state: PipelineState) -> str:
    """Route to error if injection detected or error occurred."""
    if state.get("error") or state.get("injection_detected"):
        return "error"
    return "next_node"


def route_after_qa(state: PipelineState) -> str:
    """Route to supervisor, error, or report after QA scoring."""
    if state.get("error"):
        return "error"
    if state.get("compliance_severity") == "critical":
        return "supervisor"
    return "next_node"


pipeline = get_graph()
