from src.graph.pipeline import route_after_injection, route_after_qa, route_default


def test_route_default_no_error():
    """Route to the next node when no error exists."""
    result = route_default({"error": None})

    assert result == "next_node"


def test_route_default_with_error():
    """Route to error when state has an error."""
    result = route_default({"error": "Something failed"})

    assert result == "error"


def test_route_after_injection_clean():
    """Route to the next node when no injection is detected."""
    result = route_after_injection({"error": None, "injection_detected": False})

    assert result == "next_node"


def test_route_after_injection_detected():
    """Route to error when injection is detected."""
    result = route_after_injection({"error": None, "injection_detected": True})

    assert result == "error"


def test_route_after_qa_normal():
    """Route to the next node when QA does not require supervisor review."""
    result = route_after_qa(
        {
            "error": None,
            "compliance_flag": False,
            "overall_score": 95,
        }
    )

    assert result == "next_node"


def test_route_after_qa_supervisor():
    """Route to supervisor when compliance flag is set and score is low."""
    result = route_after_qa(
        {
            "error": None,
            "compliance_flag": True,
            "overall_score": 35,
        }
    )

    assert result == "supervisor"


def test_route_after_qa_error():
    """Route to error when QA state has an error."""
    result = route_after_qa({"error": "QA failed"})

    assert result == "error"
