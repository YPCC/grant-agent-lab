from src.harness.review import review_text
from src.llm.client import complete, enrich_review, llm_status
from src.llm.config import load_llm


def test_default_llm_is_off(monkeypatch):
    monkeypatch.delenv("GRANT_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GRANT_LLM_MODEL", raising=False)
    s = load_llm()
    assert s.provider == "none"
    assert s.enabled is False
    st = llm_status()
    assert st["enabled"] is False


def test_complete_none_skips():
    out = complete("hello")
    assert out.get("skipped") is True


def test_enrich_does_not_change_grader_counts():
    text = "We will explore interesting things and advance the field."
    base = review_text(text)
    enriched = enrich_review(text, base)
    assert enriched["fatal_or_major"] == base["fatal_or_major"]
    assert enriched.get("llm", {}).get("skipped") is True


def test_vertex_status_without_project(monkeypatch):
    monkeypatch.setenv("GRANT_LLM_PROVIDER", "vertex")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("VERTEX_PROJECT", raising=False)
    st = llm_status()
    assert st["provider"] == "vertex"
    assert st["ready"] is False
