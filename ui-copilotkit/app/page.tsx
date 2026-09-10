"use client";

import { useCallback, useEffect, useState } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";

type Finding = {
  agent: string;
  severity: string;
  location: string;
  rule_id: string;
  comment: string;
  suggested_fix: string;
};

type IntakeItem = {
  id: string;
  label: string;
  group: string;
  options: string[];
  required: boolean;
  help: string;
  value: string;
  source: string;
  note: string;
  complete: boolean;
};

type Intake = {
  summary: string;
  can_submit_to_office: boolean;
  groups: { name: string; items: IntakeItem[] }[];
};

type Review = {
  filename: string;
  char_count: number;
  excerpt: string;
  readiness_score: number;
  package_ready: boolean;
  findings: Finding[];
  summary: string;
  review_docx_url?: string;
  intake?: Intake;
};

type Tracking = {
  tracking_number: string;
  status: string;
  submitted_at: string;
  upload_url: string;
  files?: string[];
  message?: string;
};

const ROLES = ["PI", "Navigator", "Office of Research Aid", "Admin"] as const;
type Role = (typeof ROLES)[number];

export default function Page() {
  const [role, setRole] = useState<Role>("PI");
  const [text, setText] = useState("");
  const [filename, setFilename] = useState("no file");
  const [review, setReview] = useState<Review | null>(null);
  const [intake, setIntake] = useState<Intake | null>(null);
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useCopilotReadable({
    description: "Current NIH grant document text extracted from the uploaded DOCX",
    value: text.slice(0, 6000),
  });
  useCopilotReadable({
    description: "Role. PI submits to the Office of Research Aid database, not NIH.",
    value: role,
  });
  useCopilotReadable({
    description: "Office of Research Aid intake form (agent-filled, human-overridable)",
    value: intake,
  });

  const runReview = useCallback(async (file?: File) => {
    setBusy(true);
    setErr("");
    setTracking(null);
    try {
      const fd = new FormData();
      if (file) fd.append("file", file);
      fd.append("use_sample", file ? "0" : "1");
      const res = await fetch("/api/review", { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const data: Review = await res.json();
      setReview(data);
      setFilename(data.filename);
      setIntake(data.intake || null);
      if ((data as any).full_text) setText((data as any).full_text);
      else if (data.excerpt) setText(data.excerpt);
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  useCopilotAction({
    name: "reviewGrantDocx",
    description: "Run Grant Reviewer + Compliance + Budget Scrutinizer + Intake agent on the R01 DOCX.",
    handler: async () => {
      await runReview();
      return review?.summary || "Review started.";
    },
  });
  useCopilotAction({
    name: "submitToOfficeOfResearchAid",
    description:
      "Submit the completed intake packet to the Office of Research Aid database (not NIH). Returns a tracking number.",
    handler: async () => {
      if (!intake?.can_submit_to_office) return "Intake form is incomplete. Override remaining unknown fields first.";
      const res = await fetch("/api/submit-office", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intake,
          findings: review?.findings || [],
          filename,
          excerpt: text.slice(0, 4000),
          role,
        }),
      });
      const data = await res.json();
      if (data.error) return data.error;
      setTracking(data);
      return data.message || `Tracking ${data.tracking_number}`;
    },
  });

  useEffect(() => {
    runReview();
  }, [runReview]);

  const override = async (id: string, value: string) => {
    if (!intake) return;
    const res = await fetch("/api/intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intake, overrides: { [id]: value } }),
    });
    if (res.ok) setIntake(await res.json());
  };

  const submitOffice = async () => {
    if (!intake) return;
    const res = await fetch("/api/submit-office", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        intake,
        findings: review?.findings || [],
        filename,
        excerpt: text.slice(0, 4000),
        role,
      }),
    });
    const data = await res.json();
    if (data.error) {
      setErr(data.error);
      return;
    }
    setTracking(data);
  };

  const canSubmit = !!intake?.can_submit_to_office;

  return (
    <>
      <header className="topbar">
        <h1>Grant Agent Lab · CopilotKit · Office of Research Aid intake</h1>
        <div>
          <span className="chip">You are {role}</span>
          <select value={role} onChange={(e) => setRole(e.target.value as Role)} style={{ marginLeft: 8, padding: "4px 8px" }}>
            {ROLES.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </div>
      </header>

      {tracking && (
        <div className="card" style={{ margin: "8px 12px 0", background: "#d5e8d4" }}>
          <b>Office tracking number: {tracking.tracking_number}</b>
          <div className="meta">
            {tracking.status} · {tracking.submitted_at} · {tracking.upload_url}
          </div>
        </div>
      )}

      <div className="layout">
        <aside className="card">
          <h2>Proposal documents</h2>
          <div className="meta">PR-2026-014 · R01 · office database (not NIH)</div>
          <p style={{ margin: "8px 0 4px", fontWeight: 650 }}>{filename}</p>
          <div className="row">
            <label className="btn">
              Upload .docx
              <input
                type="file"
                accept=".docx"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) runReview(f);
                }}
              />
            </label>
            <button className="btn" onClick={() => runReview()} disabled={busy}>
              {busy ? "Reviewing…" : "Review sample DOCX"}
            </button>
          </div>
          <p className="hint">
            Agents fill the intake form from the DOCX. You may override. Submit sends the package to the Office of Research
            Aid database — never to NIH from this screen.
          </p>
          <div className="row">
            <button className="btn primary" disabled={!canSubmit} onClick={submitOffice} id="submit-office">
              Submit to Office of Research Aid
            </button>
          </div>
          {!canSubmit && (
            <p className="hint">Intake incomplete. Answer remaining required items (PI certification is human-only).</p>
          )}
        </aside>

        <main className="card">
          <h2>Open document (extracted from DOCX)</h2>
          {err && <p style={{ color: "#9b2c2c" }}>{err}</p>}
          <div className="doc">{text || "Load a .docx or the sample Aims draft."}</div>
        </main>

        <section className="card">
          <h2>Agent findings</h2>
          {review ? (
            <>
              <div className="score">{review.readiness_score}</div>
              <div className="meta">{review.summary}</div>
              <div style={{ marginTop: 10 }}>
                {review.findings.map((f, i) => (
                  <div key={i} className={`finding ${f.severity}`}>
                    <b>
                      {f.severity.toUpperCase()} · {f.agent} · {f.rule_id}
                    </b>
                    <div className="meta">{f.location}</div>
                    <div>{f.comment}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="hint">Run a review to populate this rail.</p>
          )}
        </section>
      </div>

      <section className="card" style={{ margin: "0 12px 80px" }}>
        <h2>Office of Research Aid intake form</h2>
        <p className="meta">{intake?.summary || "Review a document so the intake agent can fill this form."}</p>
        {intake?.groups?.map((g) => (
          <div key={g.name}>
            <h3 style={{ color: "#1b4f8a", fontSize: 14 }}>{g.name}</h3>
            {g.items.map((it) => (
              <div
                key={it.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 150px 90px",
                  gap: 8,
                  alignItems: "center",
                  borderBottom: "1px solid #d7dee8",
                  padding: "8px 0",
                }}
              >
                <label title={it.help}>
                  {it.required ? "* " : ""}
                  {it.label}
                  <div className="meta">{it.note}</div>
                </label>
                <select value={it.value} onChange={(e) => override(it.id, e.target.value)}>
                  {(it.options || ["yes", "no", "unknown"]).map((o) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
                <span className="chip">{it.source}</span>
              </div>
            ))}
          </div>
        ))}
      </section>

      <CopilotSidebar
        defaultOpen
        labels={{
          title: "Grant agents",
          initial:
            "I fill the Office of Research Aid intake form from your R01 DOCX. Ask me to review, explain a field, or submit to the office database (not NIH).",
        }}
      />
    </>
  );
}
