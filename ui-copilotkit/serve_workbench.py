#!/usr/bin/env python3
"""Local workbench for R01 DOCX review (CopilotKit-pattern UI).

Official CopilotKit React sidebar lives in app/ and needs `npm install && npm run dev`.
This server always works: upload/review DOCX, findings rail, RBAC, download report.
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

SAMPLE = ROOT / "data/samples/r01-aims-draft-for-review.docx"
SCRIPT = HERE / "lib/review_grant_docx.py"
PUBLIC = HERE / "public"
PUBLIC.mkdir(exist_ok=True)
GRAPH = build_graph()
THREAD = "demo-r01"

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Grant Agent Lab · CopilotKit-pattern workbench</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--ink:#122033;--muted:#5b6b7c;--line:#d7dee8;--blue:#1b4f8a;--blue-soft:#dae8fc;--rose-soft:#f8cecc;--gold-soft:#fff2cc}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--ink)}
.top{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#0e2a4a;color:#fff}
.chip{background:#fff2cc;color:#3d3208;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:650}
.layout{display:grid;grid-template-columns:270px 1fr 340px;gap:12px;padding:12px;min-height:calc(100vh - 52px)}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
h1{font-size:15px;margin:0}h2{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 10px}
.doc{white-space:pre-wrap;font-size:13.5px;line-height:1.45;max-height:58vh;overflow:auto}
.btn{border:1px solid var(--line);background:#fff;padding:7px 12px;border-radius:7px;cursor:pointer;font:inherit}
.btn.primary{background:var(--blue);color:#fff;border-color:var(--blue)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.finding{border:1px solid var(--line);border-radius:8px;padding:8px;margin:8px 0}
.fatal,.blocker{background:var(--rose-soft)}
.major{background:var(--gold-soft)}
.warning{background:var(--blue-soft)}
.score{font-size:28px;font-weight:700;color:var(--blue)}
.meta,.hint{font-size:12px;color:var(--muted)}
.chat{position:fixed;right:16px;bottom:16px;width:340px;height:420px;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.12);display:flex;flex-direction:column;overflow:hidden;z-index:20}
.chat h3{margin:0;padding:10px 12px;background:#123;color:#fff;font-size:13px}
.msgs{flex:1;overflow:auto;padding:10px;font-size:13px}
.bubble{background:#eef3f9;border-radius:8px;padding:8px;margin:6px 0}
.bubble.me{background:#dae8fc}
.chat form{display:flex;border-top:1px solid var(--line)}
.chat input{flex:1;border:0;padding:10px;font:inherit}
</style>
</head>
<body>
<header class="top">
  <h1>Grant Agent Lab · CopilotKit-pattern workbench · R01 DOCX review</h1>
  <div>
    <span class="chip" id="rolechip">You are PI</span>
    <select id="role" onchange="onRole()">
      <option>PI</option><option>Navigator</option><option>OSPA</option><option>Admin</option>
    </select>
  </div>
</header>
<div class="layout">
  <aside class="card">
    <h2>Documents</h2>
    <div class="meta">PR-2026-014 · R01 · sample FOA</div>
    <p id="fname" style="font-weight:650">r01-aims-draft-for-review.docx</p>
    <div class="row">
      <label class="btn">Upload .docx<input id="file" type="file" accept=".docx" hidden onchange="upload(this.files[0])"></label>
      <button class="btn" onclick="review()">Review sample DOCX</button>
    </div>
    <div class="row">
      <button class="btn primary" id="freeze">Freeze for OSPA</button>
      <button class="btn" id="submit" disabled title="OSPA AOR submits after institutional approval">Submit to NIH</button>
    </div>
    <p class="hint" id="rbac">Submit stays off for PI. Switch role to OSPA to enable.</p>
    <p class="hint">Full CopilotKit React sidebar: <code>cd ui-copilotkit && npm i && npm run dev</code></p>
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
    <div class="row">
      <button class="btn" onclick="hitl('revise')">HITL: revise</button>
      <button class="btn primary" onclick="hitl('approve')">HITL: approve freeze</button>
    </div>
    <p class="hint" id="hitlmsg">Graph pauses before freeze (Part B LangGraph HITL).</p>
    <p><a class="btn primary" id="dl" href="/review-report.docx">Download review report .docx</a></p>
  </section>
</div>
<div class="chat">
  <h3>Grant agents (Copilot-style rail)</h3>
  <div class="msgs" id="msgs">
    <div class="bubble">Ask me to review the Specific Aims DOCX, explain a finding, or why PI cannot submit.</div>
  </div>
  <form onsubmit="return chat(event)">
    <input id="q" placeholder="Review this grant DOCX…" />
    <button class="btn primary" type="submit">Send</button>
  </form>
</div>
<script>
let last = null;
function onRole(){
  const r = document.getElementById('role').value;
  document.getElementById('rolechip').textContent = 'You are ' + r;
  document.getElementById('submit').disabled = !(r==='OSPA' || r==='Admin');
  document.getElementById('rbac').textContent = (r==='OSPA'||r==='Admin')
    ? 'AOR may run the submission assistant (demo). No eRA passwords stored.'
    : 'Submit stays off for role “'+r+'”. Switch to OSPA to enable.';
}
async function review(file){
  const fd = new FormData();
  if(file){ fd.append('file', file); fd.append('use_sample','0'); }
  else fd.append('use_sample','1');
  const res = await fetch('/api/review', {method:'POST', body:fd});
  last = await res.json();
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
     <div class="meta">${f.location}</div><div>${f.comment}</div>
     <div class="hint">Fix: ${f.suggested_fix}</div></div>`
  ).join('');
  document.getElementById('dl').href = d.review_docx_url || '/review-report.docx';
  const cl = d.checklist || {};
  document.getElementById('check').innerHTML = (cl.items||[]).map(it =>
    `<div class="finding ${it.status==='present'?'warning':'blocker'}">
      <b>${it.status==='present'?'✓':'✗'} ${it.label}</b>
      <div class="meta">${it.group} · ${it.id}${it.required?' · required':''}</div>
    </div>`
  ).join('') || '<p class="hint">No checklist yet.</p>';
}
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
    review().then(()=> add((last&&last.summary)||'Review complete. See the findings rail.', false));
  } else if(ql.includes('submit')){
    add('Official NIH submit is an OSPA/AOR action after Freeze. PI cannot click Submit. This assistant does not store eRA passwords.', false);
  } else if(last && last.findings && last.findings.length){
    add(last.findings.map(f=>`<b>${f.rule_id}</b> — ${f.comment}`).join('<br/>'), false);
  } else {
    add('Try “Review this grant DOCX” or switch role to OSPA to inspect submit RBAC.', false);
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
        if path.endswith(".docx"):
            # prefer latest generated report
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
        body = json.dumps(data).encode()
        self._send(200, body, "application/json")


if __name__ == "__main__":
    port = 8765
    print(f"Workbench http://127.0.0.1:{port}")
    print(f"Sample DOCX {SAMPLE}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
