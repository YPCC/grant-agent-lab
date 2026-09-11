"""Langfuse is optional. Local spans always record each guarded agent."""
from src.control_plane.guard import PolicyAsk, PolicyDenied, guard
from src.control_plane.observability import enabled, get_spans, reset_spans, status
from src.part_b_langgraph.graph import GrantGraph


def setup_function():
    reset_spans()


def test_langfuse_off_without_keys():
    assert enabled() is False
    s = status()
    assert s["langfuse"]["configured"] is False


def test_guard_records_agent_span():
    guard("GrantReviewer", "review", lambda: {"fatal_or_major": 0})
    names = [x["name"] for x in get_spans()]
    assert "GrantReviewer.review" in names
    rec = next(x for x in get_spans() if x["name"] == "GrantReviewer.review")
    assert rec["status"] == "ok"
    assert rec["agent"] == "GrantReviewer"


def test_denied_span_is_error_level():
    try:
        guard("submission_assistant", "submit_to_nih", lambda: "nope")
    except PolicyDenied:
        pass
    rec = next(x for x in get_spans() if x["action"] == "submit_to_nih")
    assert rec["status"] == "denied"
    assert rec["level"] == "ERROR"


def test_ask_span_is_warning():
    try:
        guard("package_creator", "submit_office", lambda: "x")
    except PolicyAsk:
        pass
    rec = next(x for x in get_spans() if x["action"] == "submit_office")
    assert rec["status"] == "ask"
    assert rec["level"] == "WARNING"


def test_graph_invoke_nests_agent_spans():
    g = GrantGraph()
    g.invoke(
        {"text": "Aim 1: we will study stuff.", "proposal_id": "OBS-1", "filename": "t.txt"},
        {"configurable": {"thread_id": "obs-1"}},
    )
    names = [x["name"] for x in get_spans()]
    assert "grant-graph.invoke" in names
    assert any(n.startswith("GrantReviewer.") for n in names)
    assert any(n.startswith("MissingEssentials.") for n in names)
    assert any(n.startswith("intake.") for n in names)
