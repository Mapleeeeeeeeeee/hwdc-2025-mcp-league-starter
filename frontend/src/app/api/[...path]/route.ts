import { NextRequest, NextResponse } from "next/server";
import http from "http";

// Disable the default 2-minute timeout for incoming requests
export const dynamic = "force-dynamic";

const backendUrl = process.env.DEV_BACKEND_URL || "http://localhost:8000";

// This agent will be used to handle the outgoing request to the backend
// keepAlive is important to reuse connections, improving performance
const agent = new http.Agent({
  keepAlive: true,
});

async function handler(req: NextRequest) {
  const url = new URL(req.url);
  const backendApiUrl = `${backendUrl}${url.pathname}${url.search}`;

  // Copy headers from the incoming request, removing host as it's not needed
  const headers = new Headers(req.headers);
  headers.delete("host");

  try {
    const response = await fetch(backendApiUrl, {
      method: req.method,
      headers,
      body: req.body,
      // @ts-expect-error - duplex is a valid option for streaming request bodies
      duplex: "half",
      // Use the custom agent
      agent,
    });

    // Stream the response back to the client
    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: new Headers(response.headers),
    });
  } catch (error) {
    console.error("API proxy error:", error);
    return NextResponse.json(
      { error: "API proxy failed", details: (error as Error).message },
      { status: 502 }, // 502 Bad Gateway is appropriate for a proxy failure
    );
  }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const DELETE = handler;
export const PATCH = handler;
export const HEAD = handler;
export const OPTIONS = handler;
