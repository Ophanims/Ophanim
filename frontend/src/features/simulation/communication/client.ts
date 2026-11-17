export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options, cache: "no-store", signal: options.signal ?? AbortSignal.timeout(120_000),
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const payload: unknown = await response.json();
  if (!response.ok) {
    const detail = typeof payload === "object" && payload !== null && "detail" in payload ? payload.detail : response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (!payload || typeof payload !== "object" || !("data" in payload)) throw new Error("Invalid API response");
  return payload.data as T;
}
