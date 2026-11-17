import { useState } from "react";
import { save_project } from "../../communication/projects";
import { open_map_picker } from "../../components/MapPickerModal";
import type { Project } from "../../contracts/generated";

type ListName = "ground_stations" | "rois" | "missions";
function update_path(form: Project, path: string[], value: unknown): Project {
  const next = structuredClone(form);
  let cursor = next as unknown as Record<string, unknown>;
  for (const key of path.slice(0, -1)) {
    const child = cursor[key];
    if (!child || typeof child !== "object") throw new Error(`Invalid field path: ${path.join(".")}`);
    cursor = child as Record<string, unknown>;
  }
  cursor[path[path.length - 1]] = value;
  return next;
}

export function useProjectConfig(project: Project, on_save: (project: Project) => void) {
  const [form, set_form] = useState(project);
  const [modified, set_modified] = useState(false);
  const [loading, set_loading] = useState(false);
  const [error, set_error] = useState("");
  const update_field = (path: string[], value: unknown) => {
    set_form((previous) => update_path(previous, path, value)); set_modified(true);
  };
  const update_list_item = (list_name: ListName, index: number, field: string, value: unknown) => {
    const path = list_name === "missions" ? ["experiment", "missions", String(index), field] : [list_name, String(index), field];
    update_field(path, value);
  };
  const delete_list_item = (list_name: ListName, index: number) => {
    set_form((previous) => {
      const next = structuredClone(previous);
      if (list_name === "missions") next.experiment.missions.splice(index, 1);
      else next[list_name].splice(index, 1);
      return next;
    }); set_modified(true);
  };
  const add_list_item = (list_name: ListName) => {
    set_form((previous) => {
      const next = structuredClone(previous);
      const identity = { id: "", project_id: next.project_id, name: "Untitled" };
      if (list_name === "missions") next.experiment.missions.push({ ...identity,
        target_id: "", source_node_id: "", end_node_id: "", start_time: next.experiment.start_time,
        end_time: next.experiment.end_time, duration: null });
      else if (list_name === "ground_stations") next.ground_stations.push({ ...identity, altitude_m: 0, location: { lat: 0, lon: 0 } });
      else next.rois.push({ ...identity, length: 100, width: 100, location: { lat: 0, lon: 0 } });
      return next;
    }); set_modified(true);
  };
  const select_location = async (list_name: "ground_stations" | "rois", index: number) => {
    const location = await open_map_picker();
    if (location) update_list_item(list_name, index, "location", location);
  };
  const handle_submit = async () => {
    set_loading(true); set_error("");
    try {
      const project = await save_project(form);
      set_form(project); set_modified(false); on_save(project);
    } catch (error) { set_error(error instanceof Error ? error.message : "Save failed"); }
    finally { set_loading(false); }
  };
  return { form, modified, loading, error, update_field, update_list_item,
    delete_list_item, add_list_item, select_location, handle_submit };
}
