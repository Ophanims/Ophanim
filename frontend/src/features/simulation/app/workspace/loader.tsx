"use client";
import { useEffect,useState } from "react";
import { get_record } from "../../communication/records";
import { get_project } from "../../communication/projects";
import RecordPlayback from "../../components/RecordPlayback";
import type { Project } from "../../contracts/generated";
import Workspace from "./Workspace";
import { RealtimeFramesProvider } from "./useFramesContext";

export default function WorkspaceLoader({ project_id }: { project_id: string }) {
  const [record_id, set_record_id] = useState<string | null>(null);
  const [project, set_project] = useState<Project | null>(null);
  const [error, set_error] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const selected_record_id = new URLSearchParams(window.location.search).get("record_id");
    if (selected_record_id) {
      get_record(selected_record_id, 0, controller.signal).then((window) => { set_project(window.record.project); set_record_id(selected_record_id); })
        .catch((error: Error) => { if (!controller.signal.aborted) set_error(error.message); });
      return () => controller.abort();
    }
    if (!project_id) { void Promise.resolve().then(() => set_error("No project_id selected")); return; }
    get_project(project_id, controller.signal).then((project) => { set_project(project); set_record_id(new URLSearchParams(window.location.search).get("record_id")); }).catch((error: Error) => {
      if (!controller.signal.aborted) set_error(error.message);
    });
    return () => controller.abort();
  }, [project_id]);
  if (error) return <p role="alert" className="p-8 text-red-300">{error}</p>;
  if (!project) return <p className="p-8 text-white">Loading workspace…</p>;
  return <RealtimeFramesProvider initial_algorithm={project.algorithm}><div className="flex h-full flex-col">{record_id && <RecordPlayback record_id={record_id} />}<div className="min-h-0 flex-1"><Workspace selected={project} /></div></div></RealtimeFramesProvider>;
}
