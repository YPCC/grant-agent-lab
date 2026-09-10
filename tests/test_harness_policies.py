from src.harness.policies import evaluate


def test_deny_assist():
    v = evaluate({"type": "tool_call", "data": {"name": "submit_to_nih", "arguments": {}}})
    assert v["result"] == "DENY"


def test_deny_grants_gov():
    v = evaluate({"type": "tool_call", "data": {"name": "era_commons_submit", "arguments": {}}})
    assert v["result"] == "DENY"


def test_deny_budget_invention():
    v = evaluate({"type": "tool_call", "data": {"name": "invent_budget", "arguments": {}}})
    assert v["result"] == "DENY"


def test_ask_on_office_submit():
    v = evaluate({"type": "tool_call", "data": {"name": "submit_office", "arguments": {}}})
    assert v["result"] == "ASK"


def test_allow_review():
    v = evaluate({"type": "tool_call", "data": {"name": "grant_harness_review_text", "arguments": {"text": "x"}}})
    assert v["result"] == "ALLOW"


def test_allow_checklist():
    v = evaluate({"type": "tool_call", "data": {"name": "grant_harness_score_checklist", "arguments": {}}})
    assert v["result"] == "ALLOW"
