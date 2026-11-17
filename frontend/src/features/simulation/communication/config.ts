import { API_ROUTES } from "../contracts/routes.generated";

export function route_path(route_name: keyof typeof API_ROUTES, parameters: Record<string, string | number> = {}): string {
  return API_ROUTES[route_name].replace(/\{([^}]+)\}/g, (_, name: string) => {
    if (!(name in parameters)) throw new Error(`Missing route parameter: ${name}`);
    return encodeURIComponent(parameters[name]);
  });
}
export function get_websocket_url(): string {
  const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || `http://${window.location.hostname}:8000`;
  const url = new URL(route_path("simulation_ws"), NEXT_PUBLIC_API_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}
