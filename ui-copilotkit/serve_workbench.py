#!/usr/bin/env python3
"""Local workbench: R01 DOCX review + Office of Research Aid intake + packaging.

Submit goes to the office database (not NIH). Intake is agent-filled; humans override.
"""
from __future__ import annotations

import json
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.part_b_langgraph.graph import build_graph
from src.shared.intake import apply_overrides, fill_intake
from src.shared.packaging import create_office_package

SAMPLE = ROOT / "data/samples/r01-aims-draft-for-review.docx"
SCRIPT = HERE / "lib/review_grant_docx.py"
PUBLIC = HERE / "public"
PUBLIC.mkdir(exist_ok=True)
GRAPH = build_graph()
THREAD = "demo-r01"
SESSION: dict = {"review": None, "intake": None, "tracking": None}

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Grant Agent Lab · Office of Research Aid intake</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--ink:#122033;--muted:#5b6b7c;--line:#d7dee8;--blue:#1b4f8a;--blue-soft:#dae8fc;--rose-soft:#f8cecc;--gold-soft:#fff2cc;--green-soft:#d5e8d4}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--ink)}
.top{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#0e2a4a;color:#fff}
.chip{background:#fff2cc;color:#3d3208;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:650}
.track{background:#d5e8d4;color:#1b4332;border-radius:8px;padding:8px 12px;font-weight:700;margin:8px 12px 0}
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
.item label{font-size:13px}
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
#intake-wrap{padding:0 12px 80px}
</style>
</head>
<body>
<header class="top">
  <h1>Grant Agent Lab · Office of Research Aid intake · R01</h1>
  <div>
    <span class="chip" id="rolechip">You are PI</span>
    <select id="role" onchange="onRole()">
      <option>PI</option><option>Navigator</option><option>Office of Research Aid</option><option>Admin</option>
    </select>
  </div>
</header>
<div class="track" id="trackbanner" style="display:none"></div>
<div class="layout">
  <aside class="card">
    <h2>Documents</h2>
    <div class="meta">PR-2026-014 · R01 · office intake (not NIH)</div>
    <p id="fname" style="font-weight:650">r01-aims-draft-for-review.docx</p>
    <div class="row">
      <label class="btn">Upload .docx<input id="file" type="file" accept=".docx" hidden onchange="upload(this.files[0])"></label>
      <button class="btn" onclick="review()">Review sample DOCX</button>
    </div>
    <div class="row">
      <button class="btn" onclick="hitl('approve')">HITL: approve freeze</button>
      <button class="btn primary" id="submit" disabled title="Complete the intake form first">Submit to Office of Research Aid</button>
    </div>
    <p class="hint" id="rbac">PI submits the package to the office database after the intake form is complete. This is not an NIH ASSIST submit.</p>
    <p class="hint" id="uploadlink"></p>
  </aside>
  <main class="card">
    <h2>Extracted DOCX</h2>
    <div class="doc" id="doc">Loading sample…</div>
  </main>
  <section class="card">
    <h2>Agent findings</h2>
    <div class="score" id="score">—</div>
    <div class="meta" id="sum"></div>
    <div id="findings"></div>
    <h2 style="margin-top:16px">Missing essentials</h2>
    <div id="check"></div>
    <p class="hint" id="hitlmsg">Graph pauses before freeze (Part B LangGraph HITL).</p>
  </section>
</div>
<section class="card" id="intake-wrap">
  <h2>Office of Research Aid intake form</h2>
  <p class="meta" id="intakesum">Agent fills from the document. You may override any field. Required items must be answered (not unknown). Completing the form unlocks submit; packaging agent then uploads to the office database and returns a tracking number.</p>
  <div id="intake"></div>
</section>
<div class="chat">
  <h3>Grant agents (Copilot-style rail)</h3>
  <div class="msgs" id="msgs">
    <div class="bubble">Ask me to review the DOCX, fill the intake form, or submit to the Office of Research Aid (not NIH).</div>
  </div>
  <form onsubmit="return chat(event)">
    <input id="q" placeholder="Fill the intake form…" />
    <button class="btn primary" type="submit">Send</button>
  </form>
</div>
<script>
let last = null;
let intake = null;
function onRole(){
  const r = document.getElementById('role').value;
  document.getElementById('rolechip').textContent = 'You are ' + r;
  syncSubmit();
}
function syncSubmit(){
  const r = document.getElementById('role').value;
  const okRole = (r==='PI' || r==='Navigator' || r==='Office of Research Aid' || r==='Admin');
  const ready = intake && intake.can_submit_to_office;
  document.getElementById('submit').disabled = !(okRole && ready);
  document.getElementById('rbac').textContent = ready
    ? 'Intake complete. Submit sends the package to the Office of Research Aid database (not NIH).'
    : 'Finish required intake items (agent-filled; override if needed), then submit to the office.';
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
    `<div class="finding ${f.severity}"><b>${f.severity.toUpperCase()} · ${f.agent} · ${f.rule_id}</b>
     <div class="meta">${f.location}</div><div>${f.comment}</div></div>`
  ).join('');
  const cl = d.checklist || {};
  document.getElementById('check').innerHTML = (cl.items||[]).map(it =>
    `<div class="finding ${it.status==='present'?'ok':'blocker'}">
      <b>${it.status==='present'?'✓':'✗'} ${it.label}</b>
      <div class="meta">${it.group} · ${it.id}</div>
    </div>`
  ).join('') || '<p class="hint">No checklist yet.</p>';
  if (d.intake) renderIntake(d.intake);
  if (d.tracking) showTrack(d.tracking);
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
  const form = await res.json();
  renderIntake(form);
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
  el.textContent = 'Office tracking number: ' + d.tracking_number + ' · ' + d.status + ' · uploaded ' + d.submitted_at;
  document.getElementById('uploadlink').innerHTML =
    'Package: <a href="'+d.upload_url+'">'+d.upload_url+'</a> · files: '+(d.files||[]).join(', ');
}
document.getElementById('submit').onclick = submitOffice;
async function hitl(decision){
  const res = await fetch('/api/hitl', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({decision})});
  const d = await res.json();
  document.getElementById('hitlmsg').textContent = 'HITL '+decision+' → package_ready='+d.package_ready+' · '+(d.hitl&&d.hitl.status);
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
    add((intake&&intake.summary)||'Run a review first so the intake agent can fill the form.', false);
  } else if(ql.includes('submit') || ql.includes('nih')){
    add('There is no Submit to NIH. PI completes the intake form, then submits the package to the Office of Research Aid database. A tracking number comes back here.', false);
  } else if(last && last.findings && last.findings.length){
    add(last.findings.map(f=>`<b>${f.rule_id}</b> — ${f.comment}`).join('<br/>'), false);
  } else {
    add('Try “Review this grant DOCX” or “Fill the intake form”.', false);
  }
  return false;
}
review();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[ui]", fmt % args)

    def _send(self, code, body: bytes, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, HTML.encode())
        if path.startswith("/office/packages/"):
            tracking = path.rsplit("/", 1)[-1]
            dest = ROOT / "output" / "packages" / tracking / "MANIFEST.json"
            if dest.exists():
                return self._send(200, dest.read_bytes(), "application/json")
            return self._send(404, b'{"error":"unknown tracking"}', "application/json")
        if path.endswith(".docx"):
            cand = PUBLIC / "review-report.docx"
            if path.endswith("r01-aims-draft-for-review.docx"):
                cand = SAMPLE
            if cand.exists():
                data = cand.read_bytes()
                return self._send(
                    200,
                    data,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
        return self._send(404, b"not found")

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)

        if path == "/api/hitl":
            payload = json.loads(raw.decode() or "{}")
            decision = payload.get("decision", "revise")
            if hasattr(GRAPH, "resume"):
                state = GRAPH.resume(THREAD, decision)
            else:
                state = GRAPH.invoke({"decision": decision}, {"configurable": {"thread_id": THREAD}})
            body = json.dumps({
                "decision": state.get("decision"),
                "package_ready": state.get("package_ready"),
                "hitl": state.get("hitl"),
                "checklist": state.get("checklist"),
            }).encode()
            return self._send(200, body, "application/json")

        if path == "/api/intake":
            payload = json.loads(raw.decode() or "{}")
            form = SESSION.get("intake")
            if not form:
                rev = SESSION.get("review") or {}
                form = fill_intake(rev.get("full_text") or rev.get("excerpt") or "", rev.get("filename") or "")
            form = apply_overrides(form, payload.get("overrides") or {})
            SESSION["intake"] = form
            return self._send(200, json.dumps(form).encode(), "application/json")

        if path == "/api/submit-office":
            payload = json.loads(raw.decode() or "{}")
            form = SESSION.get("intake")
            rev = SESSION.get("review") or {}
            if not form:
                return self._send(400, b'{"error":"no intake form"}', "application/json")
            try:
                snap = create_office_package(
                    filename=rev.get("filename") or "proposal.docx",
                    intake=form,
                    findings=rev.get("findings") or [],
                    text_excerpt=rev.get("excerpt") or "",
                    submitted_by=payload.get("role") or "PI",
                )
            except ValueError as e:
                return self._send(400, json.dumps({"error": str(e)}).encode(), "application/json")
            SESSION["tracking"] = snap
            return self._send(200, json.dumps(snap).encode(), "application/json")

        if path != "/api/review":
            return self._send(404, b"not found")
        import tempfile
        import subprocess

        tmp = Path(tempfile.mkdtemp(prefix="grev-"))
        src = SAMPLE
        if b"filename=" in raw and b".docx" in raw:
            idx = raw.find(b"\r\n\r\n")
            end = raw.rfind(b"\r\n--")
            if idx != -1 and end != -1:
                blob = raw[idx + 4 : end]
                src = tmp / "upload.docx"
                src.write_bytes(blob)
        out_json = tmp / "review.json"
        out_docx = tmp / "review-report.docx"
        subprocess.check_call(
            ["python3", str(SCRIPT), str(src), str(out_json), str(out_docx)]
        )
        shutil.copy(out_docx, PUBLIC / "review-report.docx")
        data = json.loads(out_json.read_text())
        data["review_docx_url"] = "/review-report.docx"
        GRAPH.invoke(
            {"text": data.get("full_text") or data.get("excerpt") or "", "findings": data.get("findings") or []},
            {"configurable": {"thread_id": THREAD}},
        )
        data["hitl"] = {"status": "awaiting_human"}
        SESSION["review"] = data
        SESSION["intake"] = data.get("intake")
        SESSION["tracking"] = None
        body = json.dumps(data).encode()
        self._send(200, body, "application/json")


if __name__ == "__main__":
    port = 8765
    print(f"Workbench http://127.0.0.1:{port}")
    print(f"Sample DOCX {SAMPLE}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
