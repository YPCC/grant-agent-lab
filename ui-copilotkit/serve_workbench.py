#!/usr/bin/env python3
"""Workbench: Part B graph + Office of Research Aid intake + harness cases.

Same GrantGraph as `python3 -m src.harness run-case`. Submit is ORA only.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.control_plane.guard import PolicyAsk, PolicyDenied
from src.harness.cases import list_cases, load_case
from src.harness.runner import run_case
from src.part_b_langgraph.graph import build_graph, snapshot
from src.shared.docx_text import extract_text
from src.shared.intake import apply_overrides

SAMPLE_DOCX = ROOT / "data/samples/r01-aims-draft-for-review.docx"
SAMPLE_TXT = ROOT / "data/samples/complete_r01_excerpt.txt"
PUBLIC = HERE / "public"
PUBLIC.mkdir(exist_ok=True)
GRAPH = build_graph()
THREAD = "demo-r01"
SESSION: dict = {"review": None, "intake": None, "tracking": None, "text": ""}

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Grant Agent Lab · Office of Research Aid</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--ink:#122033;--muted:#5b6b7c;--line:#d7dee8;--blue:#1b4f8a;--blue-soft:#dae8fc;--rose-soft:#f8cecc;--gold-soft:#fff2cc;--green-soft:#d5e8d4}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--ink)}
.top{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#0e2a4a;color:#fff}
.chip{background:#fff2cc;color:#3d3208;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:650}
.track{background:#d5e8d4;color:#1b4332;border-radius:8px;padding:8px 12px;font-weight:700;margin:8px 12px 0}
.tabs{display:flex;gap:8px;padding:8px 12px}
.tabs button{border:1px solid var(--line);background:#fff;padding:6px 12px;border-radius:7px;cursor:pointer}
.tabs button.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.layout{display:grid;grid-template-columns:250px 1fr 300px;gap:12px;padding:12px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
h1{font-size:15px;margin:0}h2{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 10px}
h3{font-size:13px;margin:14px 0 8px;color:var(--blue)}
.doc{white-space:pre-wrap;font-size:13.5px;line-height:1.45;max-height:36vh;overflow:auto}
.btn{border:1px solid var(--line);background:#fff;padding:7px 12px;border-radius:7px;cursor:pointer;font:inherit}
.btn.primary{background:var(--blue);color:#fff;border-color:var(--blue)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.finding{border:1px solid var(--line);border-radius:8px;padding:8px;margin:8px 0}
.fatal,.blocker{background:var(--rose-soft)}
.major{background:var(--gold-soft)}
.warning{background:var(--blue-soft)}
.ok{background:var(--green-soft)}
.score{font-size:28px;font-weight:700;color:var(--blue)}
.meta,.hint{font-size:12px;color:var(--muted)}
.item{display:grid;grid-template-columns:1fr 150px 90px;gap:8px;align-items:center;border-bottom:1px solid var(--line);padding:8px 0}
.item select{font:inherit;padding:4px}
.src{font-size:11px;border-radius:999px;padding:2px 8px}
.src.agent{background:var(--blue-soft)}
.src.human{background:var(--gold-soft)}
.chat{position:fixed;right:16px;bottom:16px;width:320px;height:380px;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.12);display:flex;flex-direction:column;overflow:hidden;z-index:20}
.chat h3{margin:0;padding:10px 12px;background:#123;color:#fff;font-size:13px}
.msgs{flex:1;overflow:auto;padding:10px;font-size:13px}
.bubble{background:#eef3f9;border-radius:8px;padding:8px;margin:6px 0}
.bubble.me{background:#dae8fc}
.chat form{display:flex;border-top:1px solid var(--line)}
.chat input{flex:1;border:0;padding:10px;font:inherit}
#intake-wrap,#harness-panel{padding:0 12px 80px}
pre.out{white-space:pre-wrap;font-size:12px;background:#0e2a4a;color:#e8eef5;padding:12px;border-radius:8px;max-height:50vh;overflow:auto}
.hidden{display:none}
</style>
</head>
<body>
<header class="top">
  <h1>Grant Agent Lab · Part B graph · Office of Research Aid</h1>
  <div>
    <span class="chip" id="rolechip">You are PI</span>
    <span class="chip" id="obs-chip" title="Per-agent traces. Keys enable Langfuse Cloud / self-host.">Langfuse off</span>
    <select id="role" onchange="onRole()">
      <option>PI</option><option>Navigator</option><option>Office of Research Aid</option><option>Admin</option>
    </select>
  </div>
</header>
<div class="tabs">
  <button class="on" id="tab-review" onclick="showTab('review')">Review & intake</button>
  <button id="tab-harness" onclick="showTab('harness')">Harness</button>
</div>
<div class="track" id="trackbanner" style="display:none"></div>
<div id="review-panel">
<div class="layout">
  <aside class="card">
    <h2>Documents</h2>
    <div class="meta">PR-2026-014 · R01 · one graph (harness = workbench)</div>
    <p id="fname" style="font-weight:650">sample</p>
    <div class="row">
      <label class="btn">Upload .docx<input id="file" type="file" accept=".docx,.txt" hidden onchange="upload(this.files[0])"></label>
      <button class="btn" onclick="review()">Run graph on sample</button>
    </div>
    <div class="row">
      <button class="btn" onclick="hitl('approve')">HITL: approve freeze</button>
      <button class="btn primary" id="submit" disabled>Submit to Office of Research Aid</button>
    </div>
    <p class="hint" id="rbac">Complete intake, then HITL approve. Submit is not NIH ASSIST.</p>
    <p class="hint" id="uploadlink"></p>
  </aside>
  <main class="card">
    <h2>Extracted text</h2>
    <div class="doc" id="doc">Loading sample…</div>
  </main>
  <section class="card">
    <h2>Agent findings</h2>
    <div class="score" id="score">—</div>
    <div class="meta" id="sum"></div>
    <div id="findings"></div>
    <h2 style="margin-top:16px">Missing essentials</h2>
    <div id="check"></div>
    <p class="hint" id="hitlmsg">Graph pauses before freeze (Part B HITL).</p>
  </section>
</div>
<section class="card" id="intake-wrap">
  <h2>Office of Research Aid intake form</h2>
  <p class="meta" id="intakesum">Filled by the graph intake node. Override any field. PI_CERTIFY is human-only.</p>
  <div id="intake"></div>
</section>
</div>
<section class="card hidden" id="harness-panel">
  <h2>Eval harness (same GrantGraph)</h2>
  <p class="meta">Cases from data/harness/cases. Weak aims must not freeze. Destination is Office of Research Aid only.</p>
  <div class="row" id="case-btns"></div>
  <pre class="out" id="harness-out">Select a case.</pre>
</section>
<div class="chat">
  <h3>Grant agents</h3>
  <div class="msgs" id="msgs">
    <div class="bubble">Ask me to review, fill intake, or submit to the Office of Research Aid (not NIH).</div>
  </div>
  <form onsubmit="return chat(event)">
    <input id="q" placeholder="Review this draft…" />
    <button class="btn primary" type="submit">Send</button>
  </form>
</div>
<script>
let last = null;
let intake = null;
function showTab(name){
  document.getElementById('review-panel').classList.toggle('hidden', name!=='review');
  document.getElementById('harness-panel').classList.toggle('hidden', name!=='harness');
  document.getElementById('tab-review').classList.toggle('on', name==='review');
  document.getElementById('tab-harness').classList.toggle('on', name==='harness');
  if(name==='harness') loadCases();
}
function onRole(){
  document.getElementById('rolechip').textContent = 'You are ' + document.getElementById('role').value;
  syncSubmit();
}
function syncSubmit(){
  const r = document.getElementById('role').value;
  const okRole = ['PI','Navigator','Office of Research Aid','Admin'].includes(r);
  const ready = intake && intake.can_submit_to_office;
  document.getElementById('submit').disabled = !(okRole && ready);
  document.getElementById('rbac').textContent = ready
    ? 'Intake complete. Submit = HITL approve + Office of Research Aid package (not NIH).'
    : 'Finish required intake items, then submit to the office.';
}
async function review(file){
  const fd = new FormData();
  if(file){ fd.append('file', file); fd.append('use_sample','0'); }
  else fd.append('use_sample','1');
  const res = await fetch('/api/review', {method:'POST', body:fd});
  last = await res.json();
  intake = last.intake;
  render(last);
}
function upload(f){ if(f) review(f); }
function render(d){
  document.getElementById('fname').textContent = d.filename;
  document.getElementById('doc').textContent = d.full_text || d.excerpt;
  document.getElementById('score').textContent = d.readiness_score;
  document.getElementById('sum').textContent = d.summary;
  document.getElementById('findings').innerHTML = (d.findings||[]).map(f =>
    `<div class="finding ${f.severity}"><b>${(f.severity||'').toUpperCase()} · ${f.agent} · ${f.rule_id}</b>
     <div class="meta">${f.location||''}</div><div>${f.comment||''}</div></div>`
  ).join('');
  const cl = d.checklist || {};
  document.getElementById('check').innerHTML = (cl.items||[]).map(it =>
    `<div class="finding ${it.status==='present'?'ok':'blocker'}">
      <b>${it.status==='present'?'✓':'✗'} ${it.label}</b>
      <div class="meta">${it.group||''} · ${it.id}</div>
    </div>`
  ).join('') || '<p class="hint">No checklist yet.</p>';
  if (d.intake) renderIntake(d.intake);
  if (d.package && d.package.tracking_number) showTrack(d.package);
  if (d.hitl) document.getElementById('hitlmsg').textContent = 'HITL '+ (d.hitl.status||'') + ' · can_freeze=' + (d.hitl.can_freeze);
  syncSubmit();
}
function renderIntake(form){
  intake = form;
  document.getElementById('intakesum').textContent = form.summary;
  const html = (form.groups||[]).map(g => {
    const rows = (g.items||[]).map(it => {
      const opts = (it.options||['yes','no','unknown']).map(o =>
        `<option value="${o}" ${it.value===o?'selected':''}>${o}</option>`).join('');
      return `<div class="item">
        <label title="${it.help||''}">${it.required?'* ':''}${it.label}
          <div class="meta">${it.note||''}</div></label>
        <select onchange="override('${it.id}', this.value)">${opts}</select>
        <span class="src ${it.source}">${it.source}</span>
      </div>`;
    }).join('');
    return `<h3>${g.name}</h3>${rows}`;
  }).join('');
  document.getElementById('intake').innerHTML = html;
  syncSubmit();
}
async function override(id, value){
  const res = await fetch('/api/intake', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({overrides:{[id]: value}})});
  renderIntake(await res.json());
}
async function submitOffice(){
  const role = document.getElementById('role').value;
  const res = await fetch('/api/submit-office', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({role})});
  const d = await res.json();
  if (d.error){ alert(d.error); return; }
  showTrack(d);
}
function showTrack(d){
  const el = document.getElementById('trackbanner');
  el.style.display = 'block';
  el.textContent = 'Office tracking number: ' + d.tracking_number + ' · ' + (d.status||'') + ' · ' + (d.submitted_at||'');
  document.getElementById('uploadlink').innerHTML =
    'Package: <a href="'+(d.upload_url||'')+'">'+(d.upload_url||'')+'</a>';
}
document.getElementById('submit').onclick = submitOffice;
async function hitl(decision){
  const res = await fetch('/api/hitl', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({decision})});
  const d = await res.json();
  document.getElementById('hitlmsg').textContent = 'HITL '+decision+' → package_ready='+d.package_ready+' · '+(d.hitl&&d.hitl.status);
}
async function loadCases(){
  const cases = await (await fetch('/api/harness/cases')).json();
  document.getElementById('case-btns').innerHTML = cases.map(c =>
    `<button class="btn" onclick="runCase('${c.id}')">${c.id}</button>`
  ).join('');
}
async function runCase(id){
  document.getElementById('harness-out').textContent = 'Running '+id+'…';
  const res = await fetch('/api/harness/run-case', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({case_id:id})});
  const d = await res.json();
  document.getElementById('harness-out').textContent = JSON.stringify({
    path: d.path, passed: d.grade && d.grade.passed, failed: d.grade && d.grade.failed,
    can_freeze: d.checklist && d.checklist.can_freeze,
    tracking: d.package && d.package.tracking_number,
    destination: d.package && d.package.destination,
    nih_assist: d.destination_policy && d.destination_policy.nih_assist,
    review: d.review && d.review.summary,
  }, null, 2);
}
function add(html, me){
  const el = document.createElement('div');
  el.className = 'bubble' + (me?' me':'');
  el.innerHTML = html;
  document.getElementById('msgs').appendChild(el);
  el.scrollIntoView();
}
function chat(e){
  e.preventDefault();
  const q = document.getElementById('q').value.trim();
  if(!q) return false;
  document.getElementById('q').value='';
  add(q, true);
  const ql = q.toLowerCase();
  if(ql.includes('review')){
    review().then(()=> add((last&&last.summary)||'Review complete.', false));
  } else if(ql.includes('intake') || ql.includes('form')){
    add((intake&&intake.summary)||'Run a review first.', false);
  } else if(ql.includes('nih') || ql.includes('assist')){
    add('NIH ASSIST is denied by the control plane. Submit is Office of Research Aid only.', false);
  } else if(ql.includes('submit')){
    add('Complete intake, then Submit to Office of Research Aid. That click is the HITL approve.', false);
  } else {
    add('Try “Review this draft” or open the Harness tab.', false);
  }
  return false;
}
review();
obsStatus();
async function obsStatus(){
  try {
    const s = await (await fetch('/api/observability')).json();
    const el = document.getElementById('obs-chip');
    const on = s.langfuse && (s.langfuse.enabled || s.langfuse.configured);
    el.textContent = on ? 'Langfuse on' : 'Langfuse off';
    el.title = (s.langfuse && s.langfuse.host) || '';
  } catch (e) {}
}
</script>
</body>
</html>
"""


def _sample_text() -> tuple[str, str]:
    if SAMPLE_DOCX.exists():
        try:
            return extract_text(SAMPLE_DOCX), SAMPLE_DOCX.name
        except Exception:
            pass
    if SAMPLE_TXT.exists():
        return SAMPLE_TXT.read_text(encoding="utf-8"), SAMPLE_TXT.name
    return "Sample draft unavailable.", "empty.txt"


def _save_upload(raw: bytes) -> Path | None:
    if b"filename=" not in raw:
        return None
    idx = raw.find(b"\r\n\r\n")
    end = raw.rfind(b"\r\n--")
    if idx == -1 or end == -1:
        return None
    name = "upload.bin"
    marker = b'filename="'
    if marker in raw:
        start = raw.find(marker) + len(marker)
        name = raw[start:raw.find(b'"', start)].decode("utf-8", "ignore") or name
    dest = PUBLIC / name
    dest.write_bytes(raw[idx + 4 : end])
    return dest


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[ui]", fmt % args)

    def _send(self, code, body: bytes, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        body = json.dumps(obj, default=str).encode()
        return self._send(code, body, "application/json")

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, HTML.encode())
        if path == "/api/harness/cases":
            return self._json(200, list_cases())
        if path == "/api/observability":
            from src.control_plane.observability import status as obs_status
            return self._json(200, obs_status())
        if path.startswith("/office/packages/"):
            tracking = path.rsplit("/", 1)[-1]
            dest = ROOT / "output" / "packages" / tracking / "MANIFEST.json"
            if dest.exists():
                return self._send(200, dest.read_bytes(), "application/json")
            return self._json(404, {"error": "unknown tracking"})
        return self._send(404, b"not found")

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)

        if path == "/api/hitl":
            payload = json.loads(raw.decode() or "{}")
            decision = payload.get("decision", "revise")
            state = GRAPH.resume(THREAD, decision)
            SESSION["review"] = snapshot(state)
            SESSION["intake"] = state.get("intake")
            return self._json(200, SESSION["review"])

        if path == "/api/intake":
            payload = json.loads(raw.decode() or "{}")
            form = SESSION.get("intake")
            if not form:
                return self._json(400, {"error": "no intake form"})
            form = apply_overrides(form, payload.get("overrides") or {})
            SESSION["intake"] = form
            return self._json(200, form)

        if path == "/api/submit-office":
            payload = json.loads(raw.decode() or "{}")
            form = SESSION.get("intake")
            if not form:
                return self._json(400, {"error": "no intake form"})
            try:
                state = GRAPH.resume(
                    THREAD,
                    "approve",
                    allow_package=True,
                    intake=form,
                    human_approved=True,
                )
            except (PolicyAsk, PolicyDenied) as exc:
                return self._json(403, {"error": str(exc)})
            snap = snapshot(state)
            pkg = snap.get("package")
            if not pkg:
                return self._json(
                    400,
                    {
                        "error": "Graph did not package. Need can_freeze, complete intake, and HITL approve.",
                        "package_ready": snap.get("package_ready"),
                        "intake": (snap.get("intake") or {}).get("summary"),
                    },
                )
            SESSION["tracking"] = pkg
            SESSION["review"] = snap
            return self._json(200, pkg)

        if path == "/api/harness/run-case":
            payload = json.loads(raw.decode() or "{}")
            case_id = payload.get("case_id")
            if not case_id:
                return self._json(400, {"error": "case_id required"})
            result = run_case(load_case(case_id))
            result.get("intake", {}).pop("groups", None)
            return self._json(200, result)

        if path != "/api/review":
            return self._send(404, b"not found")

        uploaded = _save_upload(raw) if raw else None
        if uploaded and uploaded.suffix.lower() in {".docx", ".txt"}:
            if uploaded.suffix.lower() == ".txt":
                text, filename = uploaded.read_text(encoding="utf-8"), uploaded.name
            else:
                text, filename = extract_text(uploaded), uploaded.name
        else:
            text, filename = _sample_text()

        state = GRAPH.invoke(
            {
                "text": text,
                "filename": filename,
                "proposal_id": "PR-2026-014",
                "mechanism": "R01",
                "allow_package": False,
            },
            {"configurable": {"thread_id": THREAD}},
        )
        data = snapshot(state)
        SESSION["review"] = data
        SESSION["intake"] = data.get("intake")
        SESSION["tracking"] = None
        SESSION["text"] = text
        return self._json(200, data)


if __name__ == "__main__":
    from src.control_plane.gates import assert_runtime_ready
    from src.control_plane.profile import current

    assert_runtime_ready()
    port = int(os.environ.get("PORT", "8080"))
    print(f"Workbench http://0.0.0.0:{port} (Part B graph, profile={current().name})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
