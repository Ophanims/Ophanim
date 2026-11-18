import type { AnalysisPoint,AnalysisWindow,RecordSnapshot,RecordWindow } from "../contracts/generated";
import { request } from "./client";
import { route_path } from "./config";
import { validate_contract } from "./contract_validation";

export async function list_records(signal?: AbortSignal, project_id?: string): Promise<RecordSnapshot[]> {
  const parameters = new URLSearchParams();
  if (project_id !== undefined) { parameters.set("project_id", project_id); parameters.set("limit", "200"); }
  const records = await request<unknown>(`${route_path("list_records")}${parameters.size ? `?${parameters}` : ""}`, { signal });
  if (!Array.isArray(records)) throw new Error("Expected record list");
  return records.map((record) => validate_contract<RecordSnapshot>(record, "RecordSnapshot"));
}
export async function get_record(record_id: string, start_frame: number, signal?: AbortSignal): Promise<RecordWindow> {
  return validate_contract<RecordWindow>(await request(`${route_path("get_record", { record_id })}?start_frame=${start_frame}&frame_limit=600`, { signal }), "RecordWindow");
}
export function get_download_url(record_id: string): string {
  return route_path("download_record", { record_id });
}

export function delete_record(record_id: string): Promise<string> {
  return request(route_path("delete_record", { record_id }), { method: "DELETE" });
}

export async function get_record_analysis(record_id: string, entity_type: AnalysisPoint["entity_type"],
  start_frame = 0, id?: string, start_point = 0, signal?: AbortSignal): Promise<AnalysisWindow> {
  const parameters = new URLSearchParams({ entity_type, start_frame: String(start_frame), start_point: String(start_point) });
  if (id !== undefined) parameters.set("id", id);
  return validate_contract<AnalysisWindow>(await request(`${route_path("get_record_analysis", { record_id })}?${parameters}`, { signal }), "AnalysisWindow");
}
