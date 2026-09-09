import { NextRequest } from "next/server";

/**
 * Lightweight CopilotKit endpoint for demos without @copilotkit/runtime.
 * Structured DOCX review uses /api/review. Free-form LLM chat needs a model key
 * and the official runtime package.
 */
export async function POST(_req: NextRequest) {
  return Response.json({
    error:
      "CopilotKit chat runtime is not configured in this demo. Use Review sample DOCX or the reviewGrantDocx action. Free-form chat needs OPENAI_API_KEY and @copilotkit/runtime.",
  });
}

export async function GET() {
  return Response.json({ status: "copilotkit-stub", chat: false, review: "/api/review" });
}
