"""Call the configured LLM. Never required for freeze / ORA packaging."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.llm.config import LlmSettings, as_public, load_llm


def llm_status() -> dict[str, Any]:
    s = load_llm()
    out = as_public(s)
    out["ready"] = False
    out["detail"] = "deterministic graders only"
    if not s.enabled:
        return out
    if s.provider == "vertex":
        out["ready"] = bool(s.project) and bool(s.model)
        out["detail"] = "Vertex AI · ADC or GOOGLE_APPLICATION_CREDENTIALS"
        if not s.project:
            out["detail"] = "set GOOGLE_CLOUD_PROJECT / VERTEX_PROJECT"
    elif s.provider == "gemini":
        out["ready"] = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
        out["detail"] = "Gemini API key in GEMINI_API_KEY or GOOGLE_API_KEY"
    elif s.provider == "openai":
        out["ready"] = bool(os.environ.get("OPENAI_API_KEY"))
        out["detail"] = "OPENAI_API_KEY"
    elif s.provider == "xai":
        out["ready"] = bool(os.environ.get("XAI_API_KEY"))
        out["detail"] = "XAI_API_KEY"
    return out


def complete(prompt: str, *, settings: LlmSettings | None = None) -> dict[str, Any]:
    s = settings or load_llm()
    if not s.enabled:
        return {"ok": False, "skipped": True, "reason": "provider=none"}
    try:
        if s.provider == "vertex":
            text = _vertex(prompt, s)
        elif s.provider == "gemini":
            text = _gemini_api(prompt, s)
        elif s.provider == "openai":
            text = _openai(prompt, s)
        elif s.provider == "xai":
            text = _xai(prompt, s)
        else:
            return {"ok": False, "skipped": True, "reason": f"unknown provider {s.provider}"}
        return {"ok": True, "text": text, "provider": s.provider, "model": s.model}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "provider": s.provider, "model": s.model}


def enrich_review(text: str, review: dict[str, Any]) -> dict[str, Any]:
    """Add an LLM narrative. Does not change checklist freeze."""
    s = load_llm()
    out = dict(review)
    if not s.enabled or not s.enrich_review:
        out["llm"] = {"skipped": True, "provider": s.provider}
        return out
    prompt = (
        "You are a study-section reviewer for an NIH R01-style Specific Aims page. "
        "The lab already applied deterministic GPA/SSRB flags. Do not invent budget dollars. "
        "Do not tell the PI to submit to NIH ASSIST. Office of Research Aid packaging only.\n\n"
        f"Deterministic summary: {review.get('summary')}\n"
        f"Flags: {json.dumps(review.get('gpa') or {})}\n\n"
        f"Aims text:\n{(text or '')[:6000]}\n\n"
        "Write 5-8 sentences: what is fundable, what is missing, one revision."
    )
    result = complete(prompt, settings=s)
    out["llm"] = result
    return out


def _vertex(prompt: str, s: LlmSettings) -> str:
    try:
        from google import genai  # type: ignore

        client = genai.Client(vertexai=True, project=s.project, location=s.location)
        resp = client.models.generate_content(model=s.model, contents=prompt)
        return getattr(resp, "text", None) or str(resp)
    except ImportError:
        pass
    token = _adc_token()
    if not token:
        raise RuntimeError("Vertex: install google-genai or set ADC (gcloud auth application-default login)")
    if not s.project:
        raise RuntimeError("Vertex: set GOOGLE_CLOUD_PROJECT")
    url = (
        f"https://{s.location}-aiplatform.googleapis.com/v1/"
        f"projects/{s.project}/locations/{s.location}/publishers/google/models/{s.model}:generateContent"
    )
    return _generate_content(url, prompt, headers={"Authorization": f"Bearer {token}"})


def _gemini_api(prompt: str, s: LlmSettings) -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY required")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{s.model}:generateContent?key={key}"
    return _generate_content(url, prompt, headers={})


def _openai(prompt: str, s: LlmSettings) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY required")
    model = s.model if s.model.startswith(("gpt-", "o")) else "gpt-4o-mini"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def _xai(prompt: str, s: LlmSettings) -> str:
    key = os.environ.get("XAI_API_KEY")
    if not key:
        raise RuntimeError("XAI_API_KEY required")
    model = s.model if "grok" in s.model else "grok-3"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def _generate_content(url: str, prompt: str, headers: dict[str, str]) -> str:
    payload = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}]}).encode()
    hdrs = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=payload, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode()[:400] or str(exc)) from exc
    cands = data.get("candidates") or []
    parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
    return "".join(p.get("text") or "" for p in parts) or json.dumps(data)[:500]


def _adc_token() -> str:
    env = os.environ.get("GOOGLE_ACCESS_TOKEN") or os.environ.get("CLOUDSDK_AUTH_ACCESS_TOKEN")
    if env:
        return env
    try:
        import google.auth
        import google.auth.transport.requests

        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(google.auth.transport.requests.Request())
        return creds.token or ""
    except Exception:
        return ""
