import { NextRequest } from "next/server";

/**
 * CopilotKit runtime endpoint.
 * If OPENAI_API_KEY (or compatible) is set, uses the official adapter.
 * Otherwise returns a short JSON hint — the workbench review rail still works
 * via /api/review and the reviewGrantDocx frontend action after a key is added.
 */
export async function POST(req: NextRequest) {
  const key = process.env.OPENAI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!key) {
    return Response.json(
      {
        error:
          "CopilotKit runtime needs OPENAI_API_KEY (or GOOGLE_API_KEY) for free-form chat. Use Review sample DOCX in the workbench — that path does not need a model key.",
      },
      { status: 200 }
    );
  }

  try {
    const { CopilotRuntime, OpenAIAdapter, copilotRuntimeNextJSAppRouterEndpoint } =
      await import("@copilotkit/runtime");
    const runtime = new CopilotRuntime();
    const serviceAdapter = new OpenAIAdapter({} as any);
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
      runtime,
      serviceAdapter,
      endpoint: "/api/copilotkit",
    });
    return handleRequest(req);
  } catch (err: any) {
    return Response.json(
      { error: "CopilotKit runtime failed to load", detail: String(err?.message || err) },
      { status: 500 }
    );
  }
}
