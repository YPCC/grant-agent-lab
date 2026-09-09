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

type Review = {
  filename: string;
  char_count: number;
  excerpt: string;
  readiness_score: number;
  package_ready: boolean;
  submit_enabled_for_pi: boolean;
  findings: Finding[];
  summary: string;
  review_docx_url?: string;
};

const ROLES = ["PI", "Navigator", "Office of Research Aid", "Admin"] as const;
type Role = (typeof ROLES)[number];

export default function Page() {
  const [role, setRole] = useState<Role>("PI");
  const [text, setText] = useState("");
  const [filename, setFilename] = useState("no file");
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useCopilotReadable({
    description: "Current NIH grant document text extracted from the uploaded DOCX",
    value: text.slice(0, 6000),
  });
  useCopilotReadable({
    description: "Current user role for RBAC. PI cannot officially submit. Office of Research Aid / AOR can approve transmit.",
    value: role,
  });
  useCopilotReadable({
    description: "Latest structured review findings JSON",
    value: review,
  });

  const runReview = useCallback(async (file?: File) => {
    setBusy(true);
    setErr("");
    try {
      const fd = new FormData();
      if (file) fd.append("file", file);
      fd.append("use_sample", file ? "0" : "1");
      const res = await fetch("/api/review", { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const data: Review = await res.json();
      setReview(data);
      setFilename(data.filename);
      if (data.excerpt) setText(data.excerpt.length < (data.char_count || 0) ? data.excerpt : data.excerpt);
      if ((data as any).full_text) setText((data as any).full_text);
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  useCopilotAction({
    name: "reviewGrantDocx",
    description:
      "Run Grant Reviewer + Compliance + Budget Scrutinizer on the uploaded or sample R01 Specific Aims DOCX.",
    handler: async () => {
      await runReview();
      return review?.summary || "Review started on the current / sample DOCX.";
    },
  });

  useEffect(() => {
    runReview();
  }, [runReview]);

  const canFreeze = role === "PI" || role === "Office of Research Aid" || role === "Admin";
  const canSubmit = role === "Office of Research Aid" || role === "Admin";

  return (
    <>
      <header className="topbar">
        <h1>Grant Agent Lab · CopilotKit workbench · R01 DOCX review</h1>
        <div>
          <span className="chip">You are {role}</span>
          {"  "}
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            style={{ marginLeft: 8, padding: "4px 8px" }}
          >
            {ROLES.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </div>
      </header>

      <div className="layout">
        <aside className="card">
          <h2>Proposal documents</h2>
          <div className="meta">PR-2026-014 · R01 · PA-25-301 (sample)</div>
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
            Agents run as jobs on the document. CopilotKit chat (right) can call{" "}
            <code>reviewGrantDocx</code>. Official submit is disabled for PI.
          </p>
          <div className="row">
            <button className="btn primary" disabled={!canFreeze || !review}>
              Freeze for Office of Research Aid
            </button>
            <button
              className="btn"
              disabled={!canSubmit}
              title={canSubmit ? "AOR transmit (demo)" : "Office of Research Aid AOR submits after institutional approval"}
            >
              Submit to NIH
            </button>
          </div>
          {!canSubmit && (
            <p className="hint">Submit stays off for role “{role}”. Switch to Office of Research Aid to see it enable.</p>
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
                    <div className="hint">Fix: {f.suggested_fix}</div>
                  </div>
                ))}
              </div>
              {review.review_docx_url && (
                <a className="btn primary" href={review.review_docx_url} style={{ display: "inline-block", marginTop: 8 }}>
                  Download review report .docx
                </a>
              )}
            </>
          ) : (
            <p className="hint">Run a review to populate this rail.</p>
          )}
        </section>
      </div>

      <CopilotSidebar
        defaultOpen
        labels={{
          title: "Grant agents",
          initial:
            "I am the Grant Reviewer rail. Ask me to review the uploaded R01 DOCX, explain a finding, or tell you why PI cannot submit. Try: “Review the Specific Aims document.”",
        }}
      />
    </>
  );
}
