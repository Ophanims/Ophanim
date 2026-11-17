import type { JobSnapshot,Project } from "../contracts/generated";
import { request } from "./client";
import { route_path } from "./config";
import { validate_contract } from "./contract_validation";

export function clear_cache(): Promise<string> { return request(route_path("clear_cache"), { method: "POST" }); }
export function get_cache_size(): Promise<number> { return request(route_path("get_cache_size")); }
export function check_cache(project: Project): Promise<Record<string, boolean>> {
  return request(route_path("check_cache"), { method: "POST", body: JSON.stringify(project) });
}
export function initial_cache(project: Project): Promise<string> {
  return request(route_path("initial_cache"), { method: "POST", body: JSON.stringify(project) });
}
export async function start_job(project: Project, job_type: "train" | "auto_test"): Promise<JobSnapshot> {
  return validate_contract<JobSnapshot>(await request(route_path("start_job", { job_type }), { method: "POST", body: JSON.stringify(project) }), "JobSnapshot");
}
export async function get_job(job_id: string): Promise<JobSnapshot> {
  return validate_contract<JobSnapshot>(await request(route_path("get_job", { job_id })), "JobSnapshot");
}
export async function cancel_job(job_id: string): Promise<JobSnapshot> {
  return validate_contract<JobSnapshot>(await request(route_path("cancel_job", { job_id }), { method: "DELETE" }), "JobSnapshot");
}
