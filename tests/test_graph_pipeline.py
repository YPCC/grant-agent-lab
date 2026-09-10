from src.harness.cases import load_case
from src.harness.runner import run_case, run_pipeline
from src.part_b_langgraph.graph import build_graph


def test_pipeline_uses_part_b_graph():
    result = run_pipeline("We will characterize stuff without a hypothesis.")
    assert result["path"] == "part_b_langgraph"
    assert result["review"]["fatal_or_major"] >= 1
    assert "checklist" in result
    assert "intake" in result
    assert result["hitl"]["status"] in {"awaiting_human", "resumed"}


def test_build_graph_has_resume():
    g = build_graph()
    assert hasattr(g, "invoke")
    assert hasattr(g, "resume")


def test_weak_aims_still_blocked_via_graph():
    result = run_case(load_case("weak_aims_vague"))
    assert result["path"] == "part_b_langgraph"
    assert result["grade"]["passed"], result["grade"]
    assert result["package"] is None
