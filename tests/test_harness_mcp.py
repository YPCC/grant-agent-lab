from src.harness.mcp_server import TOOLS, _call_tool, _handle


def test_tools_exported():
    names = {t["name"] for t in TOOLS}
    assert "grant_harness_run_case" in names
    assert "grant_harness_review_text" in names


def test_initialize_handshake():
    reply = _handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert reply["result"]["serverInfo"]["name"] == "grant-agent-harness"


def test_tool_call_review():
    out = _call_tool("grant_harness_review_text", {"text": "We will characterize stuff."})
    assert out["fatal_or_major"] >= 1


def test_tool_call_case():
    out = _call_tool("grant_harness_run_case", {"case_id": "weak_aims_vague"})
    assert out["grade"]["passed"] is True
