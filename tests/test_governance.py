"""Local vs production governance profiles."""
from __future__ import annotations

import os

import pytest

from src.control_plane.gates import GovernanceError, runtime_ready
from src.control_plane.guard import PolicyDenied, guard
from src.control_plane.identity import IdentityRequired
from src.control_plane.profile import current, reset_profile
from src.control_plane.secrets import SecretsError, assert_package_clean, redact_event
from src.harness.packaging import create_office_package


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    monkeypatch.delenv("GRANT_PROFILE", raising=False)
    monkeypatch.delenv("GRANT_ACTOR", raising=False)
    monkeypatch.delenv("GRANT_ROLE", raising=False)
    monkeypatch.delenv("GRANT_TELEMETRY_STUB", raising=False)
    monkeypatch.delenv("ERA_PASSWORD", raising=False)
    monkeypatch.setenv("GRANT_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    reset_profile()
    yield
    reset_profile()


def test_default_profile_is_local():
    assert current().name == "local"
    assert current().identity_required is False
    assert current().telemetry_required is False
    assert runtime_ready()["passed"] is True


def test_local_guard_still_denies_nih():
    with pytest.raises(PolicyDenied):
        guard("submission_assistant", "submit_to_nih", lambda: "nope")


def test_production_requires_identity(monkeypatch):
    monkeypatch.setenv("GRANT_PROFILE", "production")
    monkeypatch.setenv("GRANT_TELEMETRY_STUB", "1")
    reset_profile()
    assert current().is_production
    with pytest.raises(IdentityRequired):
        guard("GrantReviewer", "review", lambda: True)


def test_production_guard_with_identity(monkeypatch):
    monkeypatch.setenv("GRANT_PROFILE", "production")
    monkeypatch.setenv("GRANT_TELEMETRY_STUB", "1")
    monkeypatch.setenv("GRANT_ACTOR", "ada")
    monkeypatch.setenv("GRANT_ROLE", "PI")
    reset_profile()
    assert runtime_ready()["passed"] is True
    out = guard("GrantReviewer", "review", lambda: {"ok": True})
    assert out == {"ok": True}


def test_production_rejects_unknown_role(monkeypatch):
    monkeypatch.setenv("GRANT_PROFILE", "production")
    monkeypatch.setenv("GRANT_TELEMETRY_STUB", "1")
    monkeypatch.setenv("GRANT_ACTOR", "ada")
    monkeypatch.setenv("GRANT_ROLE", "root")
    reset_profile()
    with pytest.raises(IdentityRequired):
        resolve_or_guard()


def resolve_or_guard():
    guard("GrantReviewer", "review", lambda: True)


def test_production_forbids_era_password(monkeypatch):
    monkeypatch.setenv("GRANT_PROFILE", "production")
    monkeypatch.setenv("GRANT_TELEMETRY_STUB", "1")
    monkeypatch.setenv("GRANT_ACTOR", "ada")
    monkeypatch.setenv("GRANT_ROLE", "Admin")
    monkeypatch.setenv("ERA_PASSWORD", "should-not-be-here")
    reset_profile()
    report = runtime_ready()
    assert report["passed"] is False
    assert "secrets_era" in report["failed"]


def test_production_requires_telemetry(monkeypatch):
    monkeypatch.setenv("GRANT_PROFILE", "production")
    monkeypatch.setenv("GRANT_ACTOR", "ada")
    monkeypatch.setenv("GRANT_ROLE", "Admin")
    reset_profile()
    report = runtime_ready()
    assert report["passed"] is False
    assert "telemetry" in report["failed"]
    from src.part_b_langgraph.graph import GrantGraph

    with pytest.raises(GovernanceError):
        GrantGraph().invoke({"text": "x"}, {"configurable": {"thread_id": "gov"}})


def test_redact_secrets_in_audit_shape():
    red = redact_event({"password": "hunter2", "action": "review", "note": "sk-abcdefghijk"})
    assert red["password"] == "***REDACTED***"
    assert "sk-" not in str(red["note"])


def test_production_package_scan(monkeypatch):
    monkeypatch.setenv("GRANT_PROFILE", "production")
    monkeypatch.setenv("GRANT_TELEMETRY_STUB", "1")
    monkeypatch.setenv("GRANT_ACTOR", "ada")
    monkeypatch.setenv("GRANT_ROLE", "PI")
    reset_profile()
    with pytest.raises(SecretsError):
        assert_package_clean("api_key=sk-abcdefghijklmnop")
    with pytest.raises(SecretsError):
        create_office_package(text_excerpt="password=supersecret value here ok")
