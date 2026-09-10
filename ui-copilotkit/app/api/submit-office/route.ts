import { NextRequest, NextResponse } from "next/server";
import { execFile } from "child_process";
import { promises as fs } from "fs";
import os from "os";
import path from "path";
import { promisify } from "util";

const execFileAsync = promisify(execFile);
const ROOT = process.env.GRANT_LAB_ROOT || path.resolve(process.cwd(), "..");
const SCRIPT = path.join(process.cwd(), "lib/office_actions.py");

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const payload = await req.json();
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "ora-"));
  const inp = path.join(tmp, "in.json");
  const out = path.join(tmp, "out.json");
  await fs.writeFile(inp, JSON.stringify(payload));
  try {
    await execFileAsync("python3", [SCRIPT, "submit", inp, out], {
      timeout: 20000,
      env: { ...process.env, PYTHONPATH: ROOT },
    });
  } catch (e: any) {
    return NextResponse.json({ error: String(e?.stderr || e?.message || e) }, { status: 400 });
  }
  const raw = JSON.parse(await fs.readFile(out, "utf8"));
  return NextResponse.json(raw);
}
