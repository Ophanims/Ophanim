import { NextRequest } from "next/server";
const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const destination = new URL(`/api/${path.map(encodeURIComponent).join("/")}`, NEXT_PUBLIC_API_URL);
  destination.search = request.nextUrl.search;
  const response = await fetch(destination, {
    method: request.method, headers: { "Content-Type": "application/json" },
    body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.text(),
    cache: "no-store", signal: request.signal,
  });
  return new Response(response.body, { status: response.status, headers: response.headers });
}
export { forward as GET, forward as POST, forward as DELETE };
