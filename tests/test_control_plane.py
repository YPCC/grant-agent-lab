import pytest

from src.control_plane.guard import PolicyAsk, PolicyDenied, get_audit_log, guard


def test_guard_denies_nih_submit():
    with pytest.raises(PolicyDenied):
        guard("submission_assistant", "submit_to_nih", lambda: "nope")


def test_guard_asks_office_without_approval():
    with pytest.raises(PolicyAsk):
        guard("package_creator", "submit_office", lambda: "x")


def test_guard_allows_office_when_human_approved():
    out = guard("package_creator", "submit_office", lambda: "ok", human_approved=True)
    assert out == "ok"


def test_guard_allows_review():
    out = guard("GrantReviewer", "review", lambda: {"fatal_or_major": 0})
    assert out["fatal_or_major"] == 0


def test_guard_denies_budget_invention():
    with pytest.raises(PolicyDenied):
        guard("budget_scrutinizer", "invent_budget", lambda: 250000)


def test_audit_emitted():
    guard("GrantReviewer", "review", lambda: True)
    assert any(e.get("action") == "review" for e in get_audit_log())
