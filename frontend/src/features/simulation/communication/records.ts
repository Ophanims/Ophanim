import type { RecordSnapshot,RecordWindow } from "../contracts/generated";
import { request } from "./client";
import { route_path } from "./config";
import { validate_contract } from "./contract_validation";

export async function list_records(signal?: AbortSignal): Promise<RecordSnapshot[]> {
  const records = await request<unknown>(route_path("list_records"), { signal });
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
