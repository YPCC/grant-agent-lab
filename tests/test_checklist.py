from src.part_b_langgraph.graph import GrantGraph, missing_essentials_node
from src.shared.checklist import evaluate_checklist, load_catalog


def test_catalog_loads():
    cat = load_catalog()
    assert cat["mechanism"] == "R01"
    assert len(cat["items"]) >= 10


def test_sample_aims_are_incomplete():
    text = (
        "Mechanism: R01 FOA PA-25-301. Hearing is important. "
        "Aim 1. Characterize neural activity. Aim 2 building on Aim 1."
    )
    result = evaluate_checklist(text)
    missing_ids = {m["id"] for m in result["missing_required"]}
    assert "HYPOTHESIS" in missing_ids
    assert "DMS_PLAN" in missing_ids
    assert result["can_freeze"] is False
    assert result["readiness_score"] < 100


def test_hitl_pauses_then_resume():
    g = GrantGraph()
    s = g.invoke({"text": "R01 specific aim 1 hypothesis we hypothesize X causes Y"}, {"configurable": {"thread_id": "t1"}})
    assert s["hitl"]["status"] == "awaiting_human"
    s2 = g.resume("t1", "revise")
    assert s2["decision"] == "revise"
    assert s2.get("package_ready") is not True
