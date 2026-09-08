import { NextRequest, NextResponse } from "next/server";
import { execFile } from "child_process";
import { promises as fs } from "fs";
import os from "os";
import path from "path";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

const ROOT = path.resolve(process.cwd(), "..");
const SAMPLE = path.join(ROOT, "data/samples/r01-aims-draft-for-review.docx");
const SCRIPT = path.join(process.cwd(), "lib/review_grant_docx.py");

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const useSample = String(form.get("use_sample") || "1") === "1";
  const file = form.get("file");

  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "grant-rev-"));
  let src = SAMPLE;
  if (!useSample && file && file instanceof File) {
    const buf = Buffer.from(await file.arrayBuffer());
    src = path.join(tmp, file.name || "upload.docx");
    await fs.writeFile(src, buf);
  }

  const outJson = path.join(tmp, "review.json");
  const outDocx = path.join(tmp, "review-report.docx");
  const publicDocx = path.join(process.cwd(), "public", "review-report.docx");

  await execFileAsync("python3", [SCRIPT, src, outJson, outDocx], {
    timeout: 30000,
  });
  await fs.mkdir(path.join(process.cwd(), "public"), { recursive: true });
  await fs.copyFile(outDocx, publicDocx);

  const raw = JSON.parse(await fs.readFile(outJson, "utf8"));
  raw.review_docx_url = "/review-report.docx?t=" + Date.now();
  return NextResponse.json(raw);
}
