import type { Project } from "../contracts/generated";
import { request } from "./client";
import { route_path } from "./config";
import { validate_contract } from "./contract_validation";

export async function list_projects(signal?: AbortSignal): Promise<Project[]> {
  const projects = await request<unknown>(route_path("list_projects"), { signal });
  if (!Array.isArray(projects)) throw new Error("Expected project list");
  return projects.map((project) => validate_contract<Project>(project, "Project"));
}
export async function get_project(project_id: string, signal?: AbortSignal): Promise<Project> {
  return validate_contract<Project>(await request(route_path("get_project", { project_id }), { signal }), "Project");
}
export async function detect_project(project: Project): Promise<Project> {
  return validate_contract<Project>(await request(route_path("detect_project"), { method: "POST", body: JSON.stringify(project) }), "Project");
}
export async function save_project(project: Project): Promise<Project> {
  return validate_contract<Project>(await request(route_path("save_project"), { method: "POST", body: JSON.stringify(project) }), "Project");
}
export function delete_project(project_id: string): Promise<string> {
  return request(route_path("delete_project", { project_id }), { method: "DELETE" });
}
