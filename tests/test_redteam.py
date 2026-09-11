"""Static adversarial probes — DeepTeam-shaped, no extra package."""
from src.control_plane.guard import PolicyDenied, guard
from src.harness.redteam import PROBES, run_static_probes


def test_static_probes_cannot_open_nih_assist():
    out = run_static_probes()
    assert out["passed"], out["failed"]
    for p in out["probes"]:
        assert p["nih_assist"] is False
        dest = (p.get("destination") or "").upper()
        assert "NIH_ASSIST" not in dest


def test_probe_catalog_covers_goal_hijack():
    kinds = {p["kind"] for p in PROBES}
    assert "goal_hijack" in kinds
    assert "excessive_agency" in kinds


def test_guard_still_denies_during_probe_path():
    with __import__("pytest").raises(PolicyDenied):
        guard("submission_assistant", "submit_to_nih", lambda: "nope")
